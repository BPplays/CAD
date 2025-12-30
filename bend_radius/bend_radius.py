# === variables start (in millimeters) ===

thickness = 15
radius = 82



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


Spacer_thickness = thickness
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
	thickness: float = thickness
	diameter: float = radius * 2




def or_models(models):
	main_result = None

	for model in models:
		if main_result is None:
			main_result = model
		else:
			main_result = main_result.union(model)

	return main_result

def cut_models(models):
	main_result = None

	for model in models:
		if main_result is None:
			main_result = model
		else:
			main_result = main_result.cut(model)

	return main_result

def make_spacer(spacer):
	do_braces = True

	ring_thickness = 5

	outer_dia_cut = spacer.diameter * 100
	outer_dia = spacer.diameter
	inner_dia = spacer.diameter - (ring_thickness * 2)
	if inner_dia <= 0.0001:
		inner_dia = 0
		do_braces = False
	thickness = spacer.thickness

	outer_r_cut = outer_dia_cut / 2.0
	outer_r = outer_dia / 2.0
	inner_r = inner_dia / 2.0

	washer = cq.Workplane("XY").circle(outer_r).circle(inner_r).extrude(thickness)
	washer_cut = cq.Workplane("XY").circle(outer_r_cut).circle(outer_r - (ring_thickness / 2)).extrude(thickness * 10).translate((0, 0, -(thickness * 5)))

	lineX = cq.Workplane("XY").rect(outer_dia, 7).extrude(2)
	lineY = cq.Workplane("XY").rect(7, outer_dia).extrude(2)
	lineX = lineX.cut(washer_cut)
	lineY = lineY.cut(washer_cut)


	washer = (
		washer
		.faces(">Z or <Z")
		.edges()
		.fillet(1)
	)

	out = washer
	if do_braces:
		out = or_models({washer, lineX, lineY})



	return out, spacer

def loop_output(out_dir_base):

	step = Decimal("0.25")
	diameter = step
	while diameter <= Decimal('200.0'):
		radius = diameter / Decimal("2")

		out_dir = out_dir_base
		out_dir.mkdir(parents=True, exist_ok=True)

		spacer = Spacer(
			name=f"bend radius gauge {radius:.3f} mm",
			version=SemVer(1, 0, 0),
			thickness=thickness,
			diameter=float(diameter),
		)
		print(f"making \"{spacer.name}\"")

		result, spacer = make_spacer(spacer=spacer)

		name = str(out_dir.joinpath(
				f"{spacer.name} {str(spacer.version)}"
			))
		name = name.replace(".", "\u2024")
		exporters.export(
			result,
			name + ".step"
		)
		diameter += step

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
		name=f"bend radius gauge {radius} mm",
		version=SemVer(1, 0, 1),
		thickness=thickness,
		diameter=radius * 2,
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
