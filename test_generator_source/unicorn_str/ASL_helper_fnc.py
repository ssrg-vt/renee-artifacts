class ASL_helper_fnc:
	def __init__(self):
		self.shift_type = {"0": "ShiftType_LSL", "1": "ShiftType_LSR" , "2": "ShiftType_ASR", "3": "ShiftType_ROR" }

	def decode_shift(self, bvec):
		return self.shift_type[bvec]
