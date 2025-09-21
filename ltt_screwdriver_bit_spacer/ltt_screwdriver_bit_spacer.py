# === variables start ===
spacer_thickness = 2.0 # in millimeters


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
	thickness: float = spacer_thickness




def make_spacer(spacer):

	outer_dia = 22
	inner_dia = 12.0 + 0.4
	thickness = spacer.thickness

	outer_r = outer_dia / 2.0
	inner_r = inner_dia / 2.0

	washer = cq.Workplane("XY").circle(outer_r).circle(inner_r).extrude(thickness)

	half_box = (
		cq.Workplane("XY")
		  .box(outer_dia, outer_dia * 2.0, thickness * 2.0, centered=(True, True, True))
		  .translate((outer_r, 0, 0))
	)

	half_washer = washer.intersect(half_box)

	return half_washer, spacer

def loop_output(out_dir):

	step = Decimal('0.5')
	i = step
	while i <= Decimal('10.0'):

		spacer = Spacer(
			name=f"ltt screwdriver bit spacer for {Decimal('20.0') - i}mm bits",
			version=SemVer(1, 0, 0),
			thickness=spacer_thickness,
		)
		print(f"making \"{spacer.name}\"")

		result, spacer = make_spacer(spacer=spacer)
		exporters.export(
			result,
			str(out_dir.joinpath(
				f"{spacer.name} {str(spacer.version)}.step"
			))
		)
		i += step

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
		name=f"ltt screwdriver bit spacer for {Decimal(
			'20.0'
		) - Decimal(
			str(spacer_thickness)
		)}mm bits",
		version=SemVer(1, 0, 0),
		thickness=spacer_thickness,
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
