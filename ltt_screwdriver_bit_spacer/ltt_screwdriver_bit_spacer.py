# === variables start ===
spacer_thickness = 2.0 # in millimeters


# === variables end ===
from dataclasses import dataclass, field
import cadquery as cq # noqa
import cqgridfinity as cqg  # noqa
import math  # noqa
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


def main():
	wallet = Spacer(
		name="ltt screwdriver bit spacer",
		version=SemVer(1, 0, 0),
		thickness=spacer_thickness,
	)



	# Unpack the dataclass instance into the function using asdict
	holder_in = wallet
	result, holder = make_spacer(spacer=holder_in)
	show_object(result, name=holder.name+" v"+str(holder.version))


main()
