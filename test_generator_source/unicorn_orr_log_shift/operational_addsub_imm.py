import ASL_helper_fnc 
class operational_addsub_imm:
	
	def __init__(self, file_ptr,imm12):
		self.file_ptr = file_ptr
		helpers = ASL_helper_fnc.ASL_helper_fnc()
		self.file_ptr.write('\n\t %Operational\n\n')
		self.file_ptr.write('\n\tASL(po:s): type+ = [# result  : bvec[64], ')
		self.file_ptr.write('\n\t\t       operand1: {bv : bvec[64]| if n = 31 then bv = po`SP else bv = po`X(n) endif },')
		self.file_ptr.write('\n\t\toperand2: bvec[64], %= imm')
		self.file_ptr.write('\n\t\tnzcv    : bvec[4],')
		self.file_ptr.write('\n\t\tcarry_in: bit	   	   #]\n')
		self.file_ptr.write('\n\t\tp2: s = p')
		self.file_ptr.write('\n\t\tsts1: ASL(p2)\n\n')
		self.file_ptr.write('\n\t\tsts2: ASL(p2) = sts1 with [ operand2:= imm ]\n\n')
		self.file_ptr.write('\n\t\tsts3: ASL(p2) = if sub_op then sts2 with')
		self.file_ptr.write('\n\t\t[operand2:= NOT[64](sts2`operand2),')
		self.file_ptr.write('\n\t\tcarry_in:= true]')
		self.file_ptr.write('\n\t\telse sts2 with')
		self.file_ptr.write('\n\t\t[carry_in:= false] endif\n')
		self.file_ptr.write('\n\t\tIMPORTING AddWithCarry1 %[sts3`operand1, sts3`operand2, sts3`carry_in]\n')
		self.file_ptr.write('\n\t\tsts4: ASL(p2) = sts3 with [ result:= AddWithCarry1( sts3`operand1, sts3`operand2, sts3`carry_in )`return,')
		self.file_ptr.write('\n\t\tnzcv  := AddWithCarry1( sts3`operand1, sts3`operand2, sts3`carry_in )`nzcv ]\n')
		self.file_ptr.write('\n\t\tp3: s = if setflags then p2 with')
		self.file_ptr.write('\n\t\t[`NZVC:= sts4`nzcv ]')
		self.file_ptr.write('\n\t\telse p2 endif')
		self.file_ptr.write('\n\t\tpost: s = if (d = 31 & NOT setflags)')
		self.file_ptr.write('\n\t\t                  then p3 with [`SP := sts4`result]')
		self.file_ptr.write('\n\t\t\t  else p3 with [ `X(d):= sts4`result ] endif')

'''
if __name__ == '__main__':
	addsub_shift = operational_addsub_shift()
'''

