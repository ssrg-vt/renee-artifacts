OUT=opev

null  :=
space := $(null) $(null)
comma := ,

OCAMLFIND_PACKAGES=yojson str unix threads compiler-libs compiler-libs.toplevel lem

GEN_OBJS=utils lib_spec pretty_print type_spec common_values program

OBJ_NAMES=$(GEN_OBJS)

# deferred expansion allows to update PACKAGES variable in parent makefiles
OCAML_COMMON_FLAGS=-g
OCAML_OPT_FLAGS=-thread

OCAMLOPT=ocamlfind ocamlc -package $(subst $(space),$(comma),$(OCAMLFIND_PACKAGES)) \
	$(OCAML_COMMON_FLAGS) $(OCAML_OPT_FLAGS)

CMX=$(addsuffix .cmx, $(OBJ_NAMES))
CMO=$(CMX:.cmx=.cmo)

GEN_MLFILES=$(addsuffix .ml, $(GEN_OBJS))

.SUFFIXES: .o .ml .cmx .cma .cmo .cmi
.DEFAULT_GOAL: all
.PHONY: clean compile link all

all: compile link

compile:
	mkdir -p _build && cd src && \
	${OCAMLOPT} -c $(GEN_MLFILES) && \
	mv *.cm[iox] ../_build

link:
	cd _build && $(OCAMLOPT) -linkpkg $(OBJ) $(CMO) \
	-o $(OUT) && cd .. && mv _build/$(OUT) .

clean:
	rm -rf _build
