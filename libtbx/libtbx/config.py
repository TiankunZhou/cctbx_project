import sys, os, pickle
from libtbx.path import norm_join

class UserError(Exception): pass

def python_include_path(must_exist=True):
  if (sys.platform == "win32"):
    include_path = sys.prefix + r"\include"
  else:
    include_path = sys.prefix + "/include/python" + sys.version[0:3]
  include_path = norm_join(include_path)
  if (must_exist):
    assert os.path.isdir(include_path)
  return include_path

def python_api_from_include(must_exist=True):
  include_path = python_include_path(must_exist)
  if (not os.path.isdir(include_path)): return None
  modsupport_h = open(norm_join(include_path, "modsupport.h")).readlines()
  python_api_version = None
  for line in modsupport_h:
    if (line.startswith("#define")):
      flds = line.split()
      if (len(flds) == 3 and flds[1] == "PYTHON_API_VERSION"):
        python_api_version = flds[2]
        break
  assert python_api_version is not None
  return python_api_version

def python_api_version_file_name(libtbx_build):
  return norm_join(libtbx_build, "libtbx", "PYTHON_API_VERSION")

class env:

  def __init__(self):
    libtbx_build = os.environ["LIBTBX_BUILD"]
    file_name = os.path.join(libtbx_build, "libtbx_env")
    try:
      f = open(file_name)
    except:
      raise UserError("Cannot open libtbx environment file: " + file_name)
    try:
      e = pickle.load(f)
    except:
      raise UserError("Corrupt libtbx environment file: " + file_name)
    self.__dict__.update(e)
    assert self.LIBTBX_BUILD == libtbx_build
    if (not self.python_version_major_minor == sys.version_info[:2]):
      raise UserError("Python version incompatible with this build."
       + " Version used to configure: %d.%d." % self.python_version_major_minor
       + " Version used now: %d.%d." % sys.version_info[:2])

  def write_api_file(self):
    api_file_name = python_api_version_file_name(self.LIBTBX_BUILD)
    api_from_include = python_api_from_include()
    print >> open(api_file_name, "w"), api_from_include

  def dist_name(self, package_name):
    return package_name.upper() + "_DIST"

  def has_dist(self, package_name):
    return self.dist_name(package_name) in self.dist_paths

  def dist_path(self, package_name):
    return self.dist_paths[self.dist_name(package_name)]

  def current_working_directory_is_libtbx_build(self):
    return os.path.normpath(os.getcwd()) == self.LIBTBX_BUILD

def select_sconsign_dbm_module():
  if (sys.version_info[0] > 2
      or (sys.version_info[0] == 2 and sys.version_info[1] > 2)):
    import dumbdbm
    return dumbdbm
  import anydbm
  return anydbm

def sconsign_dbm_file_name(name=".sconsign.dbm"):
  dbm_module = select_sconsign_dbm_module()
  dbm_module.open(name, "c")
  return name

class include_registry:

  def __init__(self):
    self.scan_boost()
    self._had_message = {}

  def scan_boost(self, flag=00000):
    self._scan_boost = flag
    return self

  def scan_flag(self, path):
    if (not self._scan_boost and path.lower().endswith("boost")):
      if (not path in self._had_message):
        print "libtbx.scons: implicit dependency scan disabled for directory",
        print path
        self._had_message[path] = 1
      return 00000
    return 0001

  def prepend_include_switch(self, env, path):
    assert isinstance(path, str)
    return env["INCPREFIX"] + path

  def append(self, env, paths):
    assert isinstance(paths, list)
    for path in paths:
      if (self.scan_flag(path)):
        env.Append(CPPPATH=[path])
      else:
        ipath = self.prepend_include_switch(env, path)
        env.Append(CXXFLAGS=[ipath])
        env.Append(SHCXXFLAGS=[ipath])

  def prepend(self, env, paths):
    assert isinstance(paths, list)
    paths.reverse()
    for path in paths:
      if (self.scan_flag(path)):
        env.Prepend(CPPPATH=[path])
      else:
        ipath = self.prepend_include_switch(env, path)
        env.Prepend(CXXFLAGS=[ipath])
        env.Prepend(SHCXXFLAGS=[ipath])

class _build_options:

  def set(self, **kw):
    assert env().current_working_directory_is_libtbx_build()
    self.__dict__.update(kw)

build_options = _build_options()
