import ASL_helper_fnc 
class operational_addsub_shift:
	
	def __init__(self, file_ptr, shift_amount, imm6):
		self.file_ptr = file_ptr
		helpers = ASL_helper_fnc.ASL_helper_fnc()
		self.file_ptr.write('\n\t\tp1 : s  =  if v`shift = bv( 0b11 ) then throw[s]("ReservedValue()") else  p  endif' )

		self.file_ptr.write('\n\t\tp2 : s  =  if v`sf = bv( 0b0) & v`imm6(5) = bv[1]( 0b1 )(0) then throw[s]("ReservedValue()") else p1 endif ')

		self.file_ptr.write('\n\t\tshift_type : ShiftType =' + helpers.decode_shift(shift_amount)) #par

		self.file_ptr.write('\n\t\tshift_amount : int =' + imm6)

		self.file_ptr.write('\n\t %Operational\n\n')

		self.file_ptr.write('\n\t\tASL(po:s): type+ = [# result  : bvec[64], ')
		self.file_ptr.write('\n\t\toperand1: {bv : bvec[64]| bv = po`X(n)},% note 1) we can write ASL(po:s,N:int) then sts1: ASL(p2,n). 2) Try to extract the dependant type autoamtically from string processing of xml tails')
		self.file_ptr.write('\n\t\toperand2: bvec[64], %= ShiftReg(m,shift_type,shift_amount')
		self.file_ptr.write('\n\t\tnzcv    : bvec[4],')
		self.file_ptr.write('\n\t\tcarry_in: bit	   	   #]\n')
		self.file_ptr.write('\n\t\tsts1: ASL(p2)\n\n')
		self.file_ptr.write('\n\tsts2: ASL(p2) = sts1 with [ operand2:= ShiftReg(64,p2`X(m), shift_type,shift_amount) ]\n\n')


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
		self.file_ptr.write('\n\t\tpost: s = p3 with [ `X(d):= sts4`result ]')
'''
if __name__ == '__main__':
	addsub_shift = operational_addsub_shift()
'''

