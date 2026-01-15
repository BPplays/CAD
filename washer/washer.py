# === variables start ===
Spacer_thickness = 2.0 # in millimeters
Bits = 3 # number of bits you want to the spacer to cover (experimental, tested with 3)


# === variables end ===
from dataclasses import dataclass, field
import cadquery as cq  # noqa
import cqgridfinity as cqg  # noqa
import math  # noqa
from pathlib import Path # noqa
from cadquery import exporters
from decimal import Decimal
import argparse
# pylint: skip-file
if 'show_object' not in globals():
	def show_object(*args, **kwargs):
		pass


class SemVer:
	def __init__(self, major: int, minor: int, patch: int):
		self.major = major
		self.minor = minor
		self.patch = patch

	def __repr__(self):
		return f"{self.major}.{self.minor}.{self.patch}"


@dataclass
class Spacer:
	name: str = ""
	version: SemVer = field(default_factory=lambda: SemVer(1, 0, 0))
	thickness: float = Spacer_thickness
	outer_dia: float = 50
	inner_dia: float = 35
	bits: int = Bits



def make_spacer(spacer):
	if spacer.bits > 3:
		raise ValueError(
			"can't have more then 3 bit or it won't fit around the center"
		)
		# print("can't have more then 3 bit or it won't fit around the center")
		# exit(1)

	total_bits_per_side = 6

	wedge_tr = spacer.bits / total_bits_per_side
	if wedge_tr > 1:
		wedge_tr = 1
	elif wedge_tr < 0:
		wedge_tr = 0

	wedge_tr = 1

	outer_dia = spacer.outer_dia
	inner_dia = spacer.inner_dia
	thickness = spacer.thickness

	outer_r = outer_dia / 2.0
	inner_r = inner_dia / 2.0

	washer = cq.Workplane("XY").circle(outer_r).circle(inner_r).extrude(thickness)

	return washer, spacer

def loop_output(out_dir_base):

	out_dir = out_dir_base.joinpath(f"{bits} bit{'s' if bits > 1 else ''}")
	out_dir.mkdir(parents=True, exist_ok=True)

	step = Decimal('0.5')
	bit_size = step
	bit_size = Decimal("2.0")

	outer_dia = 50
	inner_dia = 35

	while bit_size <= Decimal('10.0'):
		name = f"washer {bit_size} thick"

		spacer = Spacer(
			name=name,
			version=SemVer(1, 0, 0),
			thickness=float(bit_size),
			outer_dia=outer_dia,
			inner_dia=inner_dia,
			bits=bits
		)
		print(f"making \"{spacer.name}\" for {bits} bits")

		result, spacer = make_spacer(spacer=spacer)
		exporters.export(
			result,
			str(out_dir.joinpath(
				f"{spacer.name} {str(spacer.version)}.step"
			))
		)
		bit_size += step
		break

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-l', '--loop', action="store_true",
					 help='loop over 0.5 to 10mm spacers')
	args = parser.parse_args()


	try:
		script_dir = Path(__file__).resolve().parent
	except NameError:
		print("can't get script path")

		if __name__ == "__main__":
			exit(1)
		# script_dir = Path.cwd()

	out_dir = script_dir.joinpath("out")
	out_dir.mkdir(parents=True, exist_ok=True)

	if args.loop:
		loop_output(out_dir)
		return

	spacer = Spacer(
		name=f"ltt screwdriver bit spacer for {Bits} {Decimal(
			'20.0'
		) - Decimal(
			str(Spacer_thickness)
		)}mm bits",
		version=SemVer(1, 0, 0),
		thickness=Spacer_thickness,
		bits=Bits
	)

	result, spacer = make_spacer(spacer=spacer)
	show_object(result, name=spacer.name+" v"+str(spacer.version))
	if __name__ == "__main__":
		exporters.export(
			result,
			str(out_dir.joinpath(
				f"{spacer.name} {str(spacer.version)}.step"
			))
		)


main()
