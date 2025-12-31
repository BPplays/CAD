# === variables start (in millimeters) ===

thickness = 22
radius = 16



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



Version = SemVer(1, 2, 0)

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

def filbottop(model, fillet_size, chamfer_size):
	washer = model
	washer = (
		washer
		.faces("<Z")
		.edges()
		.chamfer(chamfer_size)
	)

	washer = (
		washer
		.faces(">Z or <<Z[1]")
		.edges()
		.fillet(fillet_size)
	)
	return washer


def make_spacer(spacer):
	do_braces = True

	ring_thickness = 5

	radius = spacer.diameter / 2


	outer_dia_cut = spacer.diameter * 100
	outer_dia = spacer.diameter
	inner_dia = spacer.diameter - (ring_thickness * 2)

	if inner_dia <= 0.0001:
		inner_dia = 0
		do_braces = False

	outer_r_cut = outer_dia_cut / 2.0
	outer_r = outer_dia / 2.0
	inner_r = inner_dia / 2.0

	cur_inner_r = outer_r - (ring_thickness / 2)

	if cur_inner_r <= 0.0001:
		cur_inner_r = 0
	thickness = spacer.thickness


	washer = cq.Workplane("XY").circle(outer_r).circle(inner_r).extrude(thickness)
	washer_cut = cq.Workplane("XY").circle(outer_r_cut).circle(cur_inner_r).extrude(thickness * 10).translate((0, 0, -(thickness * 5)))

	lineX = cq.Workplane("XY").rect(outer_dia * 2, 8.5).extrude(2)
	lineY = cq.Workplane("XY").rect(8.5, outer_dia * 2).extrude(2)

	lineX = filbottop(lineX, 0.7, 0.5)
	lineY = filbottop(lineY, 0.7, 0.5)


	single_line = False
	if radius < 15.9999:
		lineX = cq.Workplane("XY").rect(outer_dia * 2, outer_dia * 2).extrude(2)
		lineY = lineX
		single_line = True


	lineX = lineX.cut(washer_cut)
	lineY = lineY.cut(washer_cut)

	profile = (
		cq.Workplane("XZ")
		.polyline([
			(0, 0),
			(2 * 4, 0),
			(2 * 4, 2 * 4),
			(0, 0)
		])
		.close()
	)

	wsize = 7.1
	wedge = profile.extrude(wsize).translate([-1, wsize / 2, 0])
	wedge = (
		wedge
		.faces("<<Z[1]")
		.edges("(>Y and >Z and <X) or (<Y and >Z and <X)")
		.fillet(1)
	)

	# return wedge, spacer



	washer = filbottop(washer, 1, 1)

	out = washer
	if do_braces:
		out = or_models({washer, lineX, lineY})

		if single_line:
			cs = radius - 5

			if cs > 2:
				cs = 2

			if math.isclose(radius, 20, abs_tol=0.04):
				cs = 1.90

			if math.isclose(radius, 20.25, abs_tol=0.03):
				cs = 1.5

			if radius > 20.25:
				cs = 1.5

			if radius > 28:
				cs = 1


			if cs >= 0.0001:
				out = (
					out
					.faces("<Z[1]")
					.edges(">X or >Y or <X or <Y")
					.chamfer(cs)
				)
		else:
			orl = {out}
			trn = ((inner_dia / 2) - 2, 0, 2)
			trans = [
				{"trn": trn, "rot": 0},
				{"trn": trn, "rot": 90},
				{"trn": trn, "rot": 180},
				{"trn": trn, "rot": -90},
			]
			for tran in trans:
				tw = wedge.translate(tran["trn"]).rotate(
					(0, 0, 0),
					(0, 0, 1),
					tran["rot"]
				)

				tw = tw.cut(washer_cut)
				orl.add(tw)
			out = or_models(orl)



	return out, spacer

def loop_output(out_dir_base):

	step = Decimal("0.25") * 2
	diameter = 4 * (Decimal("0.25") * 2)
	while diameter <= Decimal('70.0') * 2:
		radius = diameter / Decimal("2")

		out_dir = out_dir_base
		out_dir.mkdir(parents=True, exist_ok=True)

		spacer = Spacer(
			name=f"bend radius gauge {radius:.3f} mm",
			version=Version,
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

		exporters.export(
			w=result,
			fname = name + ".stl",
			tolerance = 0.0002,
			angularTolerance = 0.08,
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
		version=Version,
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
