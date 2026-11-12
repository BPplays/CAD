# === variables start ===
import profile
S_outer_dia = 50 + 0.4
S_size_to_inner = 5
Spacer_thickness = 3.30 + 0.5 # in millimeters
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


import math

import cadquery as cq
import math



def _smooth01(x: float) -> float:
	"""Cosine smoothstep: 0->1 with zero slope at both ends."""
	x = max(0.0, min(1.0, x))
	return 0.5 - 0.5 * math.cos(math.pi * x)


def angled_ramp(
	width: float,
	depth: float,
	waves: int,
	funnel_down: float,
	height: float,
	thickness: float,
	wedge_height: float | None = None,
	start_angle: float = 0.0,
	resolution_deg: float = 2.0,
) -> cq.Workplane:
	"""
	Build a smooth ring-following ramp with constant thickness.

	Parameters
	----------
	inner_radius : float
		Inner radius of the ring.
	outer_radius : float
		Outer radius of the ring.
	ang : float
		Slope angle in degrees.
	height : float
		Peak height of the ramp.
	thickness : float
		Constant body thickness.
	wedge_height : float | None
		How much height to taper back down at the end.
		None means it returns all the way to 0.
	start_angle : float
		Starting angle of the ramp, in degrees.
	resolution_deg : float
		Internal angular spacing used for loft profiles.

	Returns
	-------
	cq.Workplane
		The ramp solid.
	"""
	if height <= 0:
		raise ValueError("height must be > 0")
	if thickness <= 0:
		raise ValueError("thickness must be > 0")
	if resolution_deg <= 0:
		raise ValueError("resolution_deg must be > 0")

	if wedge_height is None:
		wedge_height = height
	if wedge_height < 0:
		raise ValueError("wedge_height must be >= 0")

	start = math.radians(start_angle)


	n_profiles = max(1, int(waves))
	n_profiles = min(999, n_profiles)

	profiles = []

	width / waves
	cutter_h = 999
	for i in range(n_profiles):
		progress = i / (n_profiles - 1)
		even = i % 2 == 0
		t = i / (n_profiles - 1)
		h = 0

		# Rectangle center sits at the mid-radius and at the mid-height of the thickness.
		# The top of the ramp is at z = h, so the rectangle center is h - thickness/2.

		x = width * progress
		y = 0
		z = (cutter_h / 2) + funnel_down

		# Plane tangent to the ring at this angle:
		# xDir points radially outward, normal points along the ring tangent.
		# xdir = (math.cos(theta), math.sin(theta), 0.0)
		# normal = (-math.sin(theta), math.cos(theta), 0.0)
		xdir = (0, 0, 1)
		normal = (1, 0, 0)

		plane = cq.Plane(
			origin=(x, y, z),
			xDir=xdir,
			normal=normal,
		)

		profile = cq.Workplane(plane).rect(999, thickness).wire().val()
		wp = cq.Workplane(plane).newObject([profile])

		# Select the vertex at minimum Y and minimum Z
		vertex = wp.vertices("<Y and <Z").val()

		# Get all original vertices
		vertices = profile.Vertices()

		# Replace the selected vertex with one moved down in Z
		down = funnel_down * -1
		if even:
			down = 0
		new_vertices = [
			v.Center() + cq.Vector(0, 0, down)
			if v.isSame(vertex)
			else v.Center()
			for v in vertices
		]

		# plane = cq.Plane(origin=(x, y, z_center))

		new_edges = [
			cq.Edge.makeLine(new_vertices[i], new_vertices[(i + 1) % len(new_vertices)])
			for i in range(len(new_vertices))
		]

		new_profile = cq.Wire.assembleEdges(new_edges)
		profiles.append(new_profile)


	# show_object(profiles)
	# return


	solid = cq.Solid.makeLoft(profiles, ruled=True)

	# show_object(solid)
	# return
	return cq.Workplane("XY").newObject([solid])


def make_spacer(spacer):
	outer_dia = spacer.outer_dia
	inner_dia = spacer.inner_dia
	thickness = spacer.thickness

	outer_r = outer_dia / 2.0
	inner_r = inner_dia / 2.0

	washer = cq.Workplane("XY").circle(outer_r).circle(inner_r).extrude(thickness)


	washer_outer = cq.Workplane("XY").circle(outer_r + 2).circle(outer_r).extrude(thickness + 2)

	washer = washer.union(washer_outer)


	washer = (
		washer
		.faces(">Z")
		.edges()
		.fillet(0.5)
	)

	washer = (
		washer
		.faces(">Z[1]")
		.edges()[1]
		.fillet(1)
	)

	return washer, spacer

def loop_output(out_dir_base):

	out_dir = out_dir_base
	out_dir.mkdir(parents=True, exist_ok=True)

	step = Decimal('0.5')
	bit_size = step
	bit_size = Decimal(Spacer_thickness)

	outer_dia = S_outer_dia
	inner_dia = S_outer_dia - S_size_to_inner

	while bit_size <= Decimal('10.0'):
		name = f"washer {bit_size}mm thick"

		spacer = Spacer(
			name=name,
			version=SemVer(1, 1, 0),
			thickness=float(bit_size),
			outer_dia=outer_dia,
			inner_dia=inner_dia,
			bits=3
		)
		print(f"making \"{spacer.name}\"")

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
	obj = angled_ramp(
		width=50,
		depth=50,
		waves=7,
		funnel_down=5,
		height=2,
		resolution_deg=20,
		thickness=25,
	)
	# return


	# obj = (
	# 	obj
	# 	.edges("<Y[0]")
	# 	.edges(">Y")
	# 	.edges("not >X")
	# 	.edges("not <X")
	# 	# .fillet(1)
	# 	.chamfer(1)
	# )
	show_object(obj)
	return


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

	if args.loop and False:
		loop_output(out_dir)
		return

	name = f"washer {Spacer_thickness}mm thick"

	spacer = Spacer(
		name=name,
		version=SemVer(1, 1, 0),
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
