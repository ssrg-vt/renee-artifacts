import matplotlib.pyplot as plt

linux_inst_class_cnt ={'condcmp_imm': 21, 'ldst_pos': 924, 'bitfield': 279, 'addsub_ext': 55, 'log_shift': 518, 'ldstpair_pre': 351, 'extract': 15, 'log_imm': 259, 'dp_2src': 108, 'pcreladdr': 418, 'condbranch': 398, 'system': 232, 'condsel': 224, 'movewide': 71, 'ldstpair_post': 346, 'ldst_regoff': 180, 'ldst_immpost': 48, 'ldstpair_off': 285, 'branch_imm': 351, 'branch_reg': 1401, 'addsub_shift': 490, 'ldstnapair_offs': 1, 'dp_3src': 74, 'dp_1src': 31, 'compbranch': 394, 'ldst_immpre': 28, 'addsub_imm': 808, 'testbranch': 102, 'exception': 36, 'loadlit': 2, 'ldst_unscaled': 28, 'ldstexcl': 146, 'condcmp_reg': 17}
zircon_inst_class_cnt ={'condcmp_imm': 7, 'ldst_pos': 241, 'bitfield': 38, 'addsub_ext': 10, 'log_shift': 123, 'ldstpair_pre': 64, 'log_imm': 73, 'dp_2src': 23, 'condcmp_reg': 4, 'condbranch': 95, 'system': 50, 'condsel': 47, 'movewide': 262, 'ldstpair_post': 64, 'ldst_regoff': 35, 'ldst_immpost': 14, 'ldstpair_off': 75, 'branch_imm': 69, 'branch_reg': 488, 'addsub_shift': 88, 'dp_3src': 18, 'dp_1src': 2, 'compbranch': 57, 'ldst_immpre': 4, 'addsub_imm': 189, 'testbranch': 13, 'exception': 17, 'ldst_unscaled': 7, 'ldstexcl': 12, 'pcreladdr': 134}

plt.bar(list(linux_inst_class_cnt.keys()), linux_inst_class_cnt.values(), color='r')
plt.xlabel("Number of Linux functions ",fontsize=20)
plt.ylabel("ARMv8 Instruction class names", fontsize=20)
plt.title("ARMv8-A64 Linux Histogram", fontsize=20)
plt.xticks(fontsize=18, rotation=90)
plt.yticks(fontsize=18, rotation=90)

plt.show()
