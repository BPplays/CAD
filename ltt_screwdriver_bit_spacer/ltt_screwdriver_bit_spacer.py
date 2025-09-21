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
	bits: int = Bits



def wedge(radius=50.0, angle_tr=0.25, height=10.0, segments=100, center_on_x=True):
    """
    Create a circular sector (pizza slice) and extrude it.
    radius      - outer radius of the slice
    angle_deg   - angle in degrees (90 == quarter, 180 == half, etc.)
    height      - extrusion height (prism)
    segments    - how many straight segments approximate the arc (more => smoother)
    center_on_x - if True, wedge is symmetric about +X axis (tip at origin)
    """
    if angle_tr <= 0:
        raise ValueError("angle_tr must be > 0")
    if angle_tr >= 1:
        # just return a full disk extruded
        return cq.Workplane("XY").circle(radius).extrude(height)

    angle_rad = angle_tr * math.tau
    half = angle_rad / 2.0
    # compute arc start/end so wedge is symmetric about +X when center_on_x=True
    if center_on_x:
        start = -half
        end = half
    else:
        # start at 0 and go positive (you can change this to any orientation)
        start = 0.0
        end = angle_rad

    # generate points along the outer arc (inclusive endpoints)
    pts = []
    for i in range(segments + 1):
        a = start + (end - start) * (i / segments)
        x = radius * math.cos(a)
        y = radius * math.sin(a)
        pts.append((x, y))

    # Build closed 2D profile:
    #   start at first arc point, follow arc to last arc point,
    #   line to center (0,0), then closed back to first arc point.
    profile_points = [pts[0]] + pts[1:] + [(0.0, 0.0)]

    # Create and extrude
    solid = cq.Workplane("XY").polyline(profile_points).close().extrude(height)
    return solid


def make_spacer(spacer):
	if spacer.bits > 3:
		print("can't have more then 3 bit or it won't fit around the center")
		exit(1)

	total_bits_per_side = 6

	wedge_tr = spacer.bits / total_bits_per_side
	if wedge_tr > 1:
		wedge_tr = 1
	elif wedge_tr < 0:
		wedge_tr = 0

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
	wedge_int = wedge(outer_dia * 10, wedge_tr, thickness * 10, 100, True)

	half_washer = washer.intersect(wedge_int)

	return half_washer, spacer

def loop_output(out_dir_base):

	for bits in range(1, 4):

		out_dir = out_dir_base.joinpath(f"{bits} bit")
		out_dir.mkdir(parents=True, exist_ok=True)

		step = Decimal('0.5')
		bit_size = step
		while bit_size <= Decimal('10.0'):

			spacer = Spacer(
				name=f"ltt screwdriver bit spacer for {Decimal('20.0') - bit_size}mm bits",
				version=SemVer(1, 0, 0),
				thickness=float(bit_size),
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
