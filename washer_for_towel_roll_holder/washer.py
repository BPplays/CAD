# === variables start ===
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


def _smooth01(t: float) -> float:
	"""C1-smooth 0..1 easing."""
	t = max(0.0, min(1.0, t))
	return 0.5 - 0.5 * math.cos(math.pi * t)


def angled_ring_ramp(
	inner_radius: float,
	outer_radius: float,
	ang: float,
	height: float,
	thickness: float,
	wedge_height: float | None = None,
	start_angle: float = 0.0,
	resolution_deg: float = 2.0,
) -> cq.Workplane:
	"""
	Smooth ring-following ramp with constant thickness.

	The shape rises along the ring up to `height`, then optionally tapers back
	down by `wedge_height`. The body is thickness-limited, so it is not a solid
	block down to the ground.

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
		Material thickness of the ramp body.
	wedge_height : float | None
		How much height to taper back down at the end.
		None means taper all the way back to zero.
	start_angle : float
		Starting angle in degrees.
	resolution_deg : float
		Internal angular spacing for the loft stations. Smaller = smoother.

	Returns
	-------
	cq.Workplane
	"""
	if inner_radius <= 0:
		raise ValueError("inner_radius must be > 0")
	if outer_radius <= inner_radius:
		raise ValueError("outer_radius must be > inner_radius")
	if ang <= 0 or ang >= 89.9:
		raise ValueError("ang should be between 0 and 90 degrees")
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

	r_mid = (inner_radius + outer_radius) / 2.0
	slope = math.tan(math.radians(ang))

	# Convert target height changes into arc lengths and then into angular spans.
	rise_arc_len = height / slope
	fall_arc_len = wedge_height / slope

	rise_theta = rise_arc_len / r_mid
	fall_theta = fall_arc_len / r_mid
	total_theta = rise_theta + fall_theta

	if total_theta <= 0:
		raise ValueError("Computed ramp span is invalid")

	start = math.radians(start_angle)

	def h_at(t: float) -> float:
		"""Height along the ramp for t in [0, 1]."""
		arc = t * total_theta

		if rise_theta > 0 and arc <= rise_theta:
			u = arc / rise_theta
			return height * _smooth01(u)

		if fall_theta > 0:
			u = (arc - rise_theta) / fall_theta
			return max(0.0, height - wedge_height * _smooth01(u))

		return height

	# Internal station count only. This is not exposed to the caller.
	stations = max(16, int(math.ceil(math.degrees(total_theta) / resolution_deg)))

	wires = []
	for i in range(stations + 1):
		t = i / stations
		theta = start + t * total_theta

		top = h_at(t)
		bottom = max(0.0, top - thickness)
		z_mid = 0.5 * (top + bottom)
		z_size = max(1e-6, top - bottom)

		x = r_mid * math.cos(theta)
		y = r_mid * math.sin(theta)

		# Plane whose x axis is vertical and y axis is radial.
		plane = cq.Plane(
			origin=(x, y, z_mid),
			xDir=(0, 0, 1),
			normal=(-math.sin(theta), math.cos(theta), 0),
		)

		wire = (
			cq.Workplane(plane)
			.rect(z_size, outer_radius - inner_radius)
			.wires()
			.val()
		)
		wires.append(wire)

	solid = cq.Solid.makeLoft(wires, ruled=False)
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
	obj = angled_ring_ramp(
		inner_radius=2,
		outer_radius=3,
		ang=60,
		height=2,
		thickness=0.5,
		wedge_height=0.25,   # set smaller for only a partial taper-down
		start_angle=0,
	)

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
