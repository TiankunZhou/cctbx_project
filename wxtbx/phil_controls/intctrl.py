
# XXX this is mostly redundant with wx.IntCtrl, but that control doesn't have
# a way to deal with None.

from wxtbx.phil_controls.text_base import ValidatedTextCtrl, TextCtrlValidator
from libtbx.utils import Sorry
import wx
import sys

class IntCtrl (ValidatedTextCtrl) :
  def __init__ (self, *args, **kwds) :
    super(IntCtrl, self).__init__(*args, **kwds)
    self.min = -sys.maxint
    self.max = sys.maxint
    self.spinner = None

  def AttachSpinner (self, spinner) :
    spinner.Bind(wx.EVT_SPIN_DOWN, self.OnSpinDown, spinner)
    spinner.Bind(wx.EVT_SPIN_UP, self.OnSpinUp, spinner)
    if (self.max is not None) :
      spinner.SetMax(self.max)
    else :
      spinner.SetMax(sys.maxint)
    if (self.min is not None) :
      spinner.SetMin(self.min)
    else :
      spinner.SetMin(-sys.maxint)
    self.spinner = spinner
    try :
      val = self.GetPhilValue()
    except Exception, e :
      print e
    else :
      if (self.GetPhilValue() is not None) :
        spinner.SetValue(self.GetPhilValue())

  def SetMin (self, min) :
    assert isinstance(min, int)
    self.min = min
    if (self.spinner is not None) :
      self.spinner.SetMin(min)

  def SetMax (self, max) :
    assert isinstance(max, int)
    self.max = max
    if (self.spinner is not None) :
      self.spinner.SetMax(max)

  def GetMin (self) :
    return self.min

  def GetMax (self) :
    return self.max

  def CreateValidator (self) :
    return IntValidator()

  def SetInt (self, value) :
    if (value is None) :
      ValidatedTextCtrl.SetValue(self, "")
    elif (isinstance(value, int)) :
      ValidatedTextCtrl.SetValue(self, str(value))
    elif (isinstance(value, str)) :
      try : # TODO remove this after testing
        value = int(value)
      except ValueError :
        raise Sorry("Inappropriate value '%s' for %s." % (value,
          self.GetName()))
      else :
        ValidatedTextCtrl.SetValue(self, str(value))
    else :
      raise TypeError("Type '%s' not allowed!" % type(value).__name__)

  def SetValue (self, value) :
    self.SetInt(value)

  def GetPhilValue (self) :
    self.Validate()
    val_str = ValidatedTextCtrl.GetValue(self)
    if (val_str == "") :
      return self.ReturnNoneIfOptional()
    return int(val_str)

  def FormatValue (self, value) :
    return str(value)

  def OnSpinUp (self, event) :
    value = self.GetPhilValue()
    if (value is None) and ((self.max is None) or (self.max > 0)) :
      self.SetValue(1)
    else :
      value += 1
      if (self.max is not None) and (value > self.max) :
        pass
      else :
        self.SetValue(value)

  def OnSpinDown (self, event) :
    value = self.GetPhilValue()
    if (value is None) and ((self.min is None) or (self.min < 0)) :
      self.SetValue(-1)
    else :
      value -= 1
      if (self.min is not None) and (value < self.min) :
        pass
      else :
        self.SetValue(value)

class IntValidator (TextCtrlValidator) :
  def CheckFormat (self, value) :
    value = int(value)
    window = self.GetWindow()
    if (value > window.GetMax()) :
      raise ValueError("Value exceeds maximum allowed (%d)." % window.GetMax())
    elif (value < window.GetMin()) :
      raise ValueError("Value is less than minimum allowed (%d)." %
        window.GetMin())
    return value # return window.FormatValue(value)

if (__name__ == "__main__") :
  app = wx.App(0)
  frame = wx.Frame(None, -1, "Integer list test")
  panel = wx.Panel(frame, -1, size=(600,400))
  txt1 = wx.StaticText(panel, -1, "Number of macro cycles:", pos=(100,180))
  int_ctrl = IntCtrl(panel, -1, pos=(300,180), size=(80,-1),
    value=3,
    name="Number of macro cycles")
  int_ctrl.SetMax(20)
  int_ctrl.SetMin(1)
  int_ctrl.SetOptional(False)
  txt2 = wx.StaticText(panel, -1, "Number of processors", pos=(100,240))
  int_ctrl2 = IntCtrl(panel, -1, pos=(300,240), size=(80,-1),
    name="Number of processors")
  spinbtn = wx.SpinButton(panel, -1, pos=(400,240))
  int_ctrl2.AttachSpinner(spinbtn)
  int_ctrl2.SetMin(1)
  btn = wx.Button(panel, -1, "Process input", pos=(400, 360))
  def OnOkay (evt) :
    int1 = int_ctrl.GetPhilValue()
    int2 = int_ctrl2.GetPhilValue()
    print type(int1).__name__, str(int1)
    print type(int2).__name__, str(int2)
  frame.Bind(wx.EVT_BUTTON, OnOkay, btn)
  frame.Fit()
  frame.Show()
  app.MainLoop()
