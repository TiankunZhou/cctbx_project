#include <boost/python/module.hpp>
#include <boost/python/class.hpp>
#include <boost/python/def.hpp>
#include <boost/python/args.hpp>

#include <simtbx/gpu/structure_factors.h>
#include <simtbx/gpu/detector.h>
#include <simtbx/gpu/simulation.h>

namespace simtbx { namespace gpu {

  struct structure_factor_wrapper
  {
    static void
    wrap()
    {
      using namespace boost::python;
      class_<simtbx::gpu::gpu_energy_channels>("gpu_energy_channels",init<>() )
        .def(init< const int& >(( arg("deviceId"))))
        .def("get_deviceID",
             &simtbx::gpu::gpu_energy_channels::get_deviceID
            )
        .def("get_nchannels",
             &simtbx::gpu::gpu_energy_channels::get_nchannels
            )
        .def("structure_factors_to_GPU_direct_cuda",
             &simtbx::gpu::gpu_energy_channels::structure_factors_to_GPU_direct_cuda,
             (arg_("dummy_int"), arg_("indices"), arg_("amplitudes"))
            )
        ;
    }
  };

  struct detector_wrapper
  {
    static void
    wrap()
    {
      using namespace boost::python;
      class_<simtbx::gpu::gpu_detector>("gpu_detector",init<>() )
        .def(init<int const&, dxtbx::model::Detector const &>(
            ( arg("deviceId"),arg("detector"))))
        .def("get_deviceID", &simtbx::gpu::gpu_detector::get_deviceID
            )
        //.def("show_summary",&simtbx::gpu::gpu_detector::show_summary)
        .def("each_image_allocate_cuda", &simtbx::gpu::gpu_detector::each_image_allocate_cuda)
        .def("each_image_free_cuda", &simtbx::gpu::gpu_detector::each_image_free_cuda)
        ;
    }
  };

  struct simulation_wrapper
  {
    static void
    wrap()
    {
      using namespace boost::python;
      class_<simtbx::gpu::exascale_api>("exascale_api",no_init )
        .def(init<const simtbx::nanoBragg::nanoBragg&>(
            ( arg("nanoBragg"))))
        .def("allocate_cuda",&simtbx::gpu::exascale_api::allocate_cuda)
        .def("add_energy_channel_from_gpu_amplitudes_cuda",
             &simtbx::gpu::exascale_api::add_energy_channel_from_gpu_amplitudes_cuda)
        .def("show",&simtbx::gpu::exascale_api::show)
        ;
    }
  };

  } // namespace gpu

  BOOST_PYTHON_MODULE(simtbx_gpu_ext)
  {
    simtbx::gpu::structure_factor_wrapper::wrap();
    simtbx::gpu::detector_wrapper::wrap();
    simtbx::gpu::simulation_wrapper::wrap();
  }
} // namespace simtbx
