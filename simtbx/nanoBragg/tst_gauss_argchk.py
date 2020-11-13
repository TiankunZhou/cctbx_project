"""
Test the GAUSS_ARGCHK facility.  Basic idea:
The GAUSS shapetype uses a call to exp() measuring RLP distance to Ewald sphere.
Most pixels on a typical pattern are far from Bragg spots, so exp() evaluates to 0.
On GPU (but not CPU) we can save lots of execution time by pretesting the argument,
    for exp(-arg), evaluate to zero if arg >= 35
Provide a backdoor to the Mullen-Holton kernel, by defining shapetype=GAUSS_ARGCHK
Test 1) standard C++ result
     3) exafel api interface to GPU, allowing fast evaluation on many energy channels
     4) exafel api interface to GPU, with GAUSS_ARGCHK

The test is derived from tst_nanoBragg_cbf_write.py
Makes dxtbx models for detector, beam , crystal
Verifies pixel intensities are reproduced
"""
from __future__ import absolute_import, division, print_function
import numpy as np
from scipy import constants
from scitbx.array_family import flex
from libtbx.test_utils import approx_equal

from cctbx import sgtbx, miller
from cctbx.crystal import symmetry
import dxtbx
from dxtbx.model.beam import BeamFactory
from dxtbx.model.crystal import CrystalFactory
from dxtbx.model.detector import DetectorFactory
from scitbx.array_family import flex
from scitbx.matrix import sqr, col
from simtbx.nanoBragg import nanoBragg, shapetype

# rough approximation to water: interpolation points for sin(theta/lambda) vs structure factor
water = flex.vec2_double([(0,2.57),(0.0365,2.58),(0.07,2.8),(0.12,5),(0.162,8),(0.18,7.32),(0.2,6.75),(0.216,6.75),(0.236,6.5),(0.28,4.5),(0.3,4.3),(0.345,4.36),(0.436,3.77),(0.5,3.17)])

def basic_crystal():
  print("Make a randomly oriented xtal")
  # make a randomly oriented crystal..
  np.random.seed(3142019)
  # make random rotation about principle axes
  x = col((-1, 0, 0))
  y = col((0, -1, 0))
  z = col((0, 0, -1))
  rx, ry, rz = np.random.uniform(-180, 180, 3)
  RX = x.axis_and_angle_as_r3_rotation_matrix(rx, deg=True)
  RY = y.axis_and_angle_as_r3_rotation_matrix(ry, deg=True)
  RZ = z.axis_and_angle_as_r3_rotation_matrix(rz, deg=True)
  M = RX*RY*RZ
  real_a = M*col((79, 0, 0))
  real_b = M*col((0, 79, 0))
  real_c = M*col((0, 0, 38))
  # dxtbx crystal description
  cryst_descr = {'__id__': 'crystal',
               'real_space_a': real_a.elems,
               'real_space_b': real_b.elems,
               'real_space_c': real_c.elems,
               'space_group_hall_symbol': ' P 4nw 2abw'}
  return CrystalFactory.from_dict(cryst_descr)

def basic_beam():
  print("Make a beam")
  # make a beam
  ENERGY = 9000
  ENERGY_CONV = 1e10*constants.c*constants.h / constants.electron_volt
  WAVELEN = ENERGY_CONV/ENERGY
  # dxtbx beam model description
  beam_descr = {'direction': (0.0, 0.0, 1.0),
             'divergence': 0.0,
             'flux': 1e11,
             'polarization_fraction': 1.,
             'polarization_normal': (0.0, 1.0, 0.0),
             'sigma_divergence': 0.0,
             'transmission': 1.0,
             'wavelength': WAVELEN}
  return BeamFactory.from_dict(beam_descr)

def basic_detector():
  # make a detector panel
  # monolithic camera description
  print("Make a dxtbx detector")
  detdist = 100.
  pixsize = 0.1
  im_shape = 1536, 1536
  det_descr = {'panels':
               [{'fast_axis': (1.0, 0.0, 0.0),
                 'slow_axis': (0.0, -1.0, 0.0),
                 'gain': 1.0,
                 'identifier': '',
                 'image_size': im_shape,
                 'mask': [],
                 'material': '',
                 'mu': 0.0,
                 'name': 'Panel',
                 'origin': (-im_shape[0]*pixsize/2., im_shape[1]*pixsize/2., -detdist),
                 'pedestal': 0.0,
                 'pixel_size': (pixsize, pixsize),
                 'px_mm_strategy': {'type': 'SimplePxMmStrategy'},
                 'raw_image_offset': (0, 0),
                 'thickness': 0.0,
                 'trusted_range': (-1e7, 1e7),
                 'type': ''}]}
  return DetectorFactory.from_dict(det_descr)

class amplitudes:
  def __init__(self, CRYSTAL):
    # make a dummy HKL table with constant HKL intensity
    # this is just to make spots
    DEFAULT_F = 1e2
    symbol = CRYSTAL.get_space_group().info().type().lookup_symbol()  # this is just P43212
    assert symbol == "P 43 21 2" # test case, start with P43212, make P1 for nanoBragg
    sgi = sgtbx.space_group_info(symbol)
    symm = symmetry(unit_cell=CRYSTAL.get_unit_cell(), space_group_info=sgi)
    miller_set = symm.build_miller_set(anomalous_flag=True, d_min=1.6, d_max=999)
    Famp = flex.double(np.ones(len(miller_set.indices())) * DEFAULT_F)
    self.Famp = miller.array(miller_set=miller_set, data=Famp).set_observation_type_xray_amplitude()

  def random_structure(self,crystal):
    """We're going to do some very approximate stuff here.  Given a unit
     cell & SG, will put typical atomic contents in the unit cell & get
     structure factors.
    """
    import random
    random.seed(0)
    from scitbx.array_family import flex
    flex.set_random_seed(0)
    from cctbx.development import random_structure

    uc_volume = crystal.get_unit_cell().volume()
    asu_volume = uc_volume / crystal.get_space_group().order_z()
    target_number_scatterers = int(asu_volume)//128 # Very approximate rule of thumb for proteins with ~50% solvent content
    element_unit = ['O']*19 + ['N']*18 + ['C']*62 + ['S']*1 + ['Fe']*1
    element_pallet = element_unit * (1 + ( target_number_scatterers//len(element_unit) ))
    assert len(element_pallet) >= target_number_scatterers
    # Ersatz hard limit to prevent excessive execution time of xray_structure() below.
    elements = element_pallet[:min(1000, target_number_scatterers)]

    xs = random_structure.xray_structure(
      space_group_info = crystal.get_space_group().info(), unit_cell = crystal.get_unit_cell(),
      elements=elements, min_distance=1.2)
    self.xs = xs

  def ersatz_correct_to_P1(self):
    primitive_xray_structure = self.xs.primitive_setting()
    P1_primitive_xray_structure = primitive_xray_structure.expand_to_p1()
    self.xs = P1_primitive_xray_structure

  def get_amplitudes(self, at_angstrom):
    # Since we are getting amplitudes for nanoBragg, let us assure they are in P1
    symbol = self.xs.space_group().info().type().lookup_symbol()
    assert symbol=="P 1", "Must be in P1 to accept amplitudes for ExaFEL GPU interface"
    # take a detour to insist on calculating anomalous contribution of every atom
    scatterers = self.xs.scatterers()
    for sc in scatterers:
      from cctbx.eltbx import henke
      expected_henke = henke.table(sc.element_symbol()).at_angstrom(at_angstrom)
      sc.fp = expected_henke.fp()
      sc.fdp = expected_henke.fdp()

    import mmtbx.command_line.fmodel
    phil2 = mmtbx.command_line.fmodel.fmodel_from_xray_structure_master_params
    params2 = phil2.extract()
    params2.high_resolution = 1.6
    params2.fmodel.k_sol = 0.35
    params2.fmodel.b_sol = 46.
    params2.structure_factors_accuracy.algorithm = "fft"
    params2.output.type = "real"
    import mmtbx
    f_model = mmtbx.utils.fmodel_from_xray_structure(
      xray_structure = self.xs,
      f_obs          = None,
      add_sigmas     = True,
      params         = params2).f_model
    #f_model.show_summary()
    return f_model

def simple_monochromatic_case(BEAM, DETECTOR, CRYSTAL, SF_model):
  Famp = SF_model.get_amplitudes(at_angstrom=BEAM.get_wavelength())

  # do the simulation
  print("\nsimple_monochromatic_case, CPU")
  SIM = nanoBragg(DETECTOR, BEAM, panel_id=0)
  SIM.Ncells_abc = (20,20,20)
  SIM.Fhkl = Famp
  SIM.Amatrix = sqr(CRYSTAL.get_A()).transpose()
  SIM.oversample = 2
  SIM.xtal_shape = shapetype.Gauss
  SIM.add_nanoBragg_spots()

  SIM.Fbg_vs_stol = water
  SIM.amorphous_sample_thick_mm = 0.02
  SIM.amorphous_density_gcm3 = 1
  SIM.amorphous_molecular_weight_Da = 18
  SIM.flux=1e12
  SIM.beamsize_mm=0.003 # square (not user specified)
  SIM.exposure_s=1.0 # multiplies flux x exposure
  SIM.progress_meter=False
  SIM.add_background()
  return SIM

def simple_monochromatic_case_GPU(BEAM, DETECTOR, CRYSTAL, SF_model, argchk=False):
  Famp = SF_model.get_amplitudes(at_angstrom=BEAM.get_wavelength())

  # do the simulation
  SIM = nanoBragg(DETECTOR, BEAM, panel_id=0)
  SIM.Ncells_abc = (20,20,20)
  SIM.Fhkl = Famp
  SIM.Amatrix = sqr(CRYSTAL.get_A()).transpose()
  SIM.oversample = 2
  if argchk:
    print("\nmonochromatic case, GPU argchk")
    SIM.xtal_shape = shapetype.Gauss_argchk
  else:
    print("\nmonochromatic case, GPU no argchk")
    SIM.xtal_shape = shapetype.Gauss
  SIM.add_nanoBragg_spots_cuda()

  SIM.Fbg_vs_stol = water
  SIM.amorphous_sample_thick_mm = 0.02
  SIM.amorphous_density_gcm3 = 1
  SIM.amorphous_molecular_weight_Da = 18
  SIM.flux=1e12
  SIM.beamsize_mm=0.003 # square (not user specified)
  SIM.exposure_s=1.0 # multiplies flux x exposure
  SIM.progress_meter=False
  SIM.add_background()
  return SIM

class several_wavelength_case:
 def __init__(self, BEAM, DETECTOR, CRYSTAL, SF_model):
  SIM = nanoBragg(DETECTOR, BEAM, panel_id=0)
  print("\nassume three energy channels")
  self.wavlen = flex.double([BEAM.get_wavelength()-0.002, BEAM.get_wavelength(), BEAM.get_wavelength()+0.002])
  self.flux = flex.double([(1./6.)*SIM.flux, (3./6.)*SIM.flux, (2./6.)*SIM.flux])
  self.sfall_channels = {}
  for x in range(len(self.wavlen)):
    self.sfall_channels[x] = SF_model.get_amplitudes(at_angstrom = self.wavlen[x])
  self.DETECTOR = DETECTOR
  self.BEAM = BEAM
  self.CRYSTAL = CRYSTAL

 def several_wavelength_case_for_CPU(self):
  SIM = nanoBragg(self.DETECTOR, self.BEAM, panel_id=0)
  for x in range(len(self.wavlen)):
    SIM.flux = self.flux[x]
    SIM.wavelength_A = self.wavlen[x]
    print("CPUnanoBragg_API+++++++++++++ Wavelength %d=%.6f, Flux %.6e, Fluence %.6e"%(
            x, SIM.wavelength_A, SIM.flux, SIM.fluence))
    SIM.Fhkl = self.sfall_channels[x]
    SIM.Ncells_abc = (20,20,20)
    SIM.Amatrix = sqr(self.CRYSTAL.get_A()).transpose()
    SIM.oversample = 2
    SIM.xtal_shape = shapetype.Gauss
    SIM.interpolate = 0
    SIM.add_nanoBragg_spots()

  SIM.wavelength_A = self.BEAM.get_wavelength()
  SIM.Fbg_vs_stol = water
  SIM.amorphous_sample_thick_mm = 0.02
  SIM.amorphous_density_gcm3 = 1
  SIM.amorphous_molecular_weight_Da = 18
  SIM.flux=1e12
  SIM.beamsize_mm=0.003 # square (not user specified)
  SIM.exposure_s=1.0 # multiplies flux x exposure
  SIM.progress_meter=False
  SIM.add_background()
  return SIM

 def modularized_exafel_api_for_GPU(self, argchk=False):
  from simtbx.nanoBragg import gpu_energy_channels
  gpu_channels_singleton = gpu_energy_channels (deviceId = 0)

  SIM = nanoBragg(self.DETECTOR, self.BEAM, panel_id=0)
  SIM.device_Id = 0

  assert gpu_channels_singleton.get_deviceID()==SIM.device_Id
  assert gpu_channels_singleton.get_nchannels() == 0 # uninitialized
  for x in range(len(self.flux)):
          gpu_channels_singleton.structure_factors_to_GPU_direct_cuda(
           x, self.sfall_channels[x].indices(), self.sfall_channels[x].data())
  assert gpu_channels_singleton.get_nchannels() == len(self.flux)
  SIM.Ncells_abc = (20,20,20)
  SIM.Amatrix = sqr(self.CRYSTAL.get_A()).transpose()
  SIM.oversample = 2
  if argchk:
    print("\npolychromatic GPU argchk")
    SIM.xtal_shape = shapetype.Gauss_argchk
  else:
    print("\npolychromatic GPU no argchk")
    SIM.xtal_shape = shapetype.Gauss
  SIM.interpolate = 0
  # allocate GPU arrays
  from simtbx.nanoBragg import exascale_api
  gpu_simulation = exascale_api(nanoBragg = SIM)
  gpu_simulation.allocate_cuda()

  from simtbx.nanoBragg import gpu_detector as gpud
  gpu_detector = gpud(deviceId=SIM.device_Id, detector=self.DETECTOR)
  gpu_detector.each_image_allocate_cuda()

  # loop over energies
  for x in range(len(self.flux)):
      SIM.flux = self.flux[x]
      SIM.wavelength_A = self.wavlen[x]
      print("USE_EXASCALE_API+++++++++++++ Wavelength %d=%.6f, Flux %.6e, Fluence %.6e"%(
            x, SIM.wavelength_A, SIM.flux, SIM.fluence))
      gpu_simulation.add_energy_channel_from_gpu_amplitudes_cuda(
        x, gpu_channels_singleton, gpu_detector)

  per_image_scale_factor = 1.0
  gpu_detector.scale_in_place_cuda(per_image_scale_factor) # apply scale directly on GPU
  SIM.wavelength_A = self.BEAM.get_wavelength() # return to canonical energy for subsequent background

  cuda_background = True
  if cuda_background:
      SIM.Fbg_vs_stol = water
      SIM.amorphous_sample_thick_mm = 0.02
      SIM.amorphous_density_gcm3 = 1
      SIM.amorphous_molecular_weight_Da = 18
      SIM.flux=1e12
      SIM.beamsize_mm=0.003 # square (not user specified)
      SIM.exposure_s=1.0 # multiplies flux x exposure
      gpu_simulation.add_background_cuda(gpu_detector)

      # deallocate GPU arrays afterward
      gpu_detector.write_raw_pixels_cuda(SIM)  # updates SIM.raw_pixels from GPU
      gpu_detector.each_image_free_cuda()
  else:
      # deallocate GPU arrays up front
      gpu_detector.write_raw_pixels_cuda(SIM)  # updates SIM.raw_pixels from GPU
      gpu_detector.each_image_free_cuda()

      SIM.Fbg_vs_stol = water
      SIM.amorphous_sample_thick_mm = 0.02
      SIM.amorphous_density_gcm3 = 1
      SIM.amorphous_molecular_weight_Da = 18
      SIM.flux=1e12
      SIM.beamsize_mm=0.003 # square (not user specified)
      SIM.exposure_s=1.0 # multiplies flux x exposure
      SIM.progress_meter=False
      SIM.add_background()
  return SIM

def diffs(labelA, A, labelB, B):
  diff = A-B
  min = flex.min(diff); mean = flex.mean(diff); max = flex.max(diff)
  print("Pixel differences between %s and %s, minimum=%.4f mean=%.4f maximum=%.4f"%(
       labelA, labelB, min, mean, max))
  assert min > -1.0
  assert max < 1.0

if __name__=="__main__":
  # make the dxtbx objects
  BEAM = basic_beam()
  DETECTOR = basic_detector()
  CRYSTAL = basic_crystal()
  SF_model = amplitudes(CRYSTAL)
  # Famp = SF_model.Famp # simple uniform amplitudes
  SF_model.random_structure(CRYSTAL)
  SF_model.ersatz_correct_to_P1()

  print("\n# Use case 1.  Simple monochromatic X-rays")
  SIM = simple_monochromatic_case(BEAM, DETECTOR, CRYSTAL, SF_model)
  SIM.to_smv_format(fileout="test_full_001.img")
  SIM.to_cbf("test_full_001.cbf")

  SIM2 = simple_monochromatic_case_GPU(BEAM, DETECTOR, CRYSTAL, SF_model, argchk=False)
  SIM3 = simple_monochromatic_case_GPU(BEAM, DETECTOR, CRYSTAL, SF_model, argchk=True)
  assert approx_equal(SIM.raw_pixels, SIM2.raw_pixels)
  assert approx_equal(SIM.raw_pixels, SIM3.raw_pixels)

  print("\n# Use case 2.  Three-wavelength polychromatic source")
  SWC = several_wavelength_case(BEAM, DETECTOR, CRYSTAL, SF_model)
  SIM = SWC.several_wavelength_case_for_CPU()
  SIM.to_smv_format(fileout="test_full_002.img")
  SIM.to_cbf("test_full_002.cbf")

  print("\n# Use case modularized api")
  SIM4 = SWC.modularized_exafel_api_for_GPU(argchk=False)
  SIM4.to_cbf("test_full_004.cbf")
  diffs("CPU",SIM.raw_pixels, "GPU",SIM4.raw_pixels)
  SIM5 = SWC.modularized_exafel_api_for_GPU(argchk=True)
  diffs("CPU",SIM.raw_pixels, "GPU argchk",SIM5.raw_pixels)
  #assert approx_equal(SIM.raw_pixels, SIM2.raw_pixels)
  #assert approx_equal(SIM.raw_pixels, SIM3.raw_pixels)

print("OK")
