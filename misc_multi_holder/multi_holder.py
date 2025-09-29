from dataclasses import dataclass, field
from cadquery import exporters
from pathlib import Path # noqa

hole_margin_small = 0.6
hole_margin_normal = 0.4


class SemVer:
	def __init__(self, major: int, minor: int, patch: int):
		self.major = major
		self.minor = minor
		self.patch = patch

	def __repr__(self):
		return f"{self.major}.{self.minor}.{self.patch}"


@dataclass
class Holder:
	name: str = ""
	version: SemVer = field(default_factory=lambda: SemVer(1, 0, 0))

	# Hole dimensions and related values
	hole_size_flat: float = 0.5
	# For a 20mm application: hole_depth = 6.5; for 50mm: hole_depth = 15 (using 15)
	hole_depth: float = 15.0

	# Fill value (for 20mm use 7, for 50mm use 18; using 18)
	fill_mm: float = 18.0

	# Grid fin parameters
	gridfin_height: float = 7.0
	hole_num_x: int = 5
	gridfin_x: int = 2
	hole_num_y: int = 4
	gridfin_y: int = 2

	# Chamfer size: for 20mm use 1.1; for 50mm use 2 (using 2)
	hole_chamfer_size: float = 2.0

	# Hole properties for circular holes
	hole_circle: bool = True
	increase_copies: int = 1
	increase_amount: float = 0.5
	hole_max_size: float = 10.0
	hole_min_size: float = 0.5
	increase_loop_after: int = 20

	# Padding values
	edge_padding: float = 0.0
	x_padding: float = 6.0
	y_padding: float = 6.0

	# Y uppies
	y_uppies: float = 12.0

	# No lip options
	no_lip: bool = True
	no_lip_upper_size: float = 2.0
	no_lip_fillet_size: float = 0.3


doesnt_exist_script_dir = "script dir doesn't exist"


# # for hex 6.35mm bit hole_size_flat = 6.35 + 0.4
# hole_size_flat = 0.5
# # good for 20mm hole_depth = 6.5
#
# # good for 50mm hole_depth = 15
# hole_depth = 15
# # good for 20mm 7
# # good for 50mm 18
# fill_mm = 18
# # good for 20mm 3
# # good for 20mm 7
# gridfin_height = 7
#
# hole_num_x = 5
# gridfin_x = 2
#
# hole_num_y = 4
# gridfin_y = 2
#
# # good for 20mm 1.1
# # good for 50mm 2
# hole_chamfer_size = 2
#
# hole_circle = True
# # increase only works for circle
# increase_copies = 1
# increase_amount = 0.5
# hole_max_size = 10
# hole_min_size = 0.5
# increase_loop_after = 20
#
# edge_padding = 0
# x_padding = 6
# y_padding = 6
#
#
# y_uppies = 12
#
# no_lip = True
# no_lip_upper_size = 2
# no_lip_fillet_size = 0.3





import cqgridfinity as cqg  # noqa
import math  # noqa
if 'show_object' not in globals():
	def show_object(*args, **kwargs):
		pass
# pylint: skip-file


def get_move_xy(
	size_dw,
	xy_full_padding,
	hole_size,
	hole_num,
	uppies=0,
):
	if hole_num > 1:
		move = (((size_dw) - ((2 * xy_full_padding) + (uppies / 2)) - hole_size) / (hole_num - 1))
	else:
		move = (((size_dw) - ((2 * xy_full_padding) + (uppies / 2)) - hole_size))

	return move



def make_holder(holder):
	hole_size_flat = holder.hole_size_flat
	hole_depth = holder.hole_depth
	fill_mm = holder.fill_mm
	gridfin_height = holder.gridfin_height
	hole_num_x = holder.hole_num_x
	gridfin_x = holder.gridfin_x
	hole_num_y = holder.hole_num_y
	gridfin_y = holder.gridfin_y
	hole_chamfer_size = holder.hole_chamfer_size
	hole_circle = holder.hole_circle
	increase_copies = holder.increase_copies
	increase_amount = holder.increase_amount
	hole_max_size = holder.hole_max_size
	hole_min_size = holder.hole_min_size
	increase_loop_after = holder.increase_loop_after
	edge_padding = holder.edge_padding
	x_padding = holder.x_padding
	y_padding = holder.y_padding
	y_uppies = holder.y_uppies
	no_lip = holder.no_lip
	no_lip_upper_size = holder.no_lip_upper_size
	no_lip_fillet_size = holder.no_lip_fillet_size




	gf_hi_size = 7
	gf_wid_size = 42
	gf_padding = 2.95
	gf_lip_size = 3.8  # this is exactly correct
	hex_short_to_long = 1.1547

	hole_size_pointy = hole_size_flat * hex_short_to_long
	if hole_circle:
		hole_size_pointy = hole_size_flat


	def to_sr(n):
		return n / (gf_hi_size * gridfin_height)
		# return ((n / ((gf_hi_size-(0.9623333333+1.2)) * height)) * -1) + 1
		# return ((n / ((gf_hi_size) * height)) * -1) + 1
		# return ((n / (gf_size_t_bot * height)) * -1) + 1


	# gf_size_t_bot = gf_lip_size + top_to_fill
	sr = to_sr(fill_mm)
	# if sr < 0:
	#     top_to_fill = (gf_hi_size * (height))


	# gf_size_t_bot = gf_lip_size + top_to_fill
	print(sr)
	# no_lip = True
	bh = cqg.GridfinityBox(
		gridfin_x,
		gridfin_y,
		gridfin_height,
		length_div=0,
		width_div=0,
		holes=False,
		no_lip=no_lip,
		scoops=False,
		labels=False,
		solid=True,
		solid_ratio=sr
	)

	# bh = cqg.
	# make the base
	result = (
		bh.cq_obj
		# .faces(">Z")
		# .workplane()
	)

	size_wid = gf_wid_size * gridfin_x
	size_dep = gf_wid_size * gridfin_y

	# move_x = (((size_wid)) / (hole_num_x+1))
	z_face_flat = "-2"

	x_full_padding = gf_padding+x_padding
	y_full_padding = gf_padding+y_padding

	start_hor = (-(size_wid) / 2) + (hole_size_pointy/2) + x_full_padding

	start_virt = (-(size_dep-y_uppies) / 2) + (hole_size_flat / 2) + y_full_padding

	result_pre_hold_edges = (
		result
		.faces(">Z[-2]")
		.edges()
	)
	# show_object(result_pre_hold_edges)



	move_x = get_move_xy(size_wid, x_full_padding, hole_size_pointy, hole_num_x)
	move_y = get_move_xy(size_dep, y_full_padding, hole_size_flat, hole_num_y, y_uppies)


	# hole_size_cir = hole_size_flat
	total_loops = 0

	hole_size_cir_base = (hole_size_flat / 2)
	for i2 in range(hole_num_y):
		for i in range(hole_num_x):
			if not hole_circle:
				result = result.faces(f">Z[{z_face_flat}]").workplane().moveTo(
					(
						start_hor+(i*move_x)
					), start_virt+(
						i2*move_y
					)).polygon(
						6,
						hole_size_pointy
					).cutBlind(
						-(hole_depth)
					)

			if hole_circle:
				hole_size_pointy = hole_size_flat

				move_x = get_move_xy(size_wid, x_full_padding, hole_size_pointy, hole_num_x)
				move_y = get_move_xy(size_dep, y_full_padding, hole_size_flat, hole_num_y, y_uppies)

				# hole_size = (hole_size_flat + (increase_amount * (math.floor((i + i2) / 2) % increase_loop_after)))  # noqa
				# hole_size = (hole_size_flat + (increase_amount * ((math.floor(((i+1) * (i2+1)) / increase_copies) % increase_loop_after)+1)))  # noqa



				if total_loops % increase_loop_after == 0:
					hole_size_cir_base = (hole_size_flat / 2)


				print(hole_size_cir_base)

				if hole_size_cir_base > (hole_max_size / 2):
					hole_size_cir = (hole_max_size / 2)
				elif hole_size_cir_base < (hole_min_size / 2):
					hole_size_cir = (hole_min_size / 2)
				else:
					hole_size_cir = hole_size_cir_base

				if hole_size_cir < (1.6 / 2):
					hole_size_cir += (hole_margin_small / 2)
				else:
					hole_size_cir += (hole_margin_normal / 2)

				result = result.faces(f">Z[{z_face_flat}]").workplane().moveTo(
					(
						start_hor+(i*move_x)
					), start_virt+(
						i2*move_y
					)).circle(
						hole_size_cir
					).cutBlind(
						-(hole_depth)
					)

				if total_loops % increase_copies == 0:
					hole_size_cir_base += (increase_amount / 2)

			total_loops += 1

	if hole_chamfer_size > 0:

		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
			.edges()
			.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
			# # ignore 4 longest edges, should always be the edge of the box
			# .sort(lambda edge: edge.Length())[::-1][4:]
			#
			# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
			# # .filter(lambda edge: edge.isCircle())
			.chamfer(hole_chamfer_size)
		)

		# if not hole_circle:
		#     result = (
		#         result
		#         .faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
		#         .edges("%LINE")   # Select all straight edges
		#         # ignore 4 longest edges, should always be the edge of the box
		#         .sort(lambda edge: edge.Length())[::-1][4:]
		#         .chamfer(hole_chamfer_size)
		#     )
		# if hole_circle:
		#     result = (
		#         result
		#         .faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
		#         # .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
		#         .edges()
		#         .filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
		#         # # ignore 4 longest edges, should always be the edge of the box
		#         # .sort(lambda edge: edge.Length())[::-1][4:]
		#         #
		#         # .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
		#         # # .filter(lambda edge: edge.isCircle())
		#         .chamfer(hole_chamfer_size)
		#     )
		#
		#     # all_edges = result.faces(">Z[-2]").edges().val()
		#     # filtered_edges = [edge for edge in all_edges if edge not in result_pre_hold_edges]
		#     #
		#     # result = result.edges(filtered_edges).chamfer(hole_chamfer_size)


	# if no_lip and True == False:


	if no_lip:
		cut_size = no_lip_upper_size
		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			.workplane(offset=no_lip_upper_size)
			.rect(size_wid*2, size_dep*2)  # Create a rectangle of width and depth

			.cutBlind((bh.height))
		)

		result = (
			result
			.faces(">Z")  # Select the bottom face of the hexagonal holes
			.edges("%LINE")   # Select all straight edges
			.fillet(no_lip_fillet_size)
		)

	# Render the solid
	return result, holder
	# bh.save_stl_file()
	# Output a STL file of box:
	# gf_box_3x2x5_holes_scoops_labels.stl


def loop_output(out_dir, holders):

	for holder in holders:
		# if holder.name != "aaa battery holder":
		# 	continue
		result, holder = make_holder(holder=holder)
		show_object(result, name=f"{holder.name} v{str(holder.version)}")

		if __name__ == "__main__" and (out_dir != doesnt_exist_script_dir):
			exporters.export(
				result,
				str(out_dir.joinpath(
					f"{holder.name} v{str(holder.version)}.step"
				))
			)


def main():
	holders = []

	holders.append(Holder(
		name="drill bit holder",
		version=SemVer(1, 0, 0),

		hole_size_flat=0.5,
		hole_depth=15.0,
		fill_mm=18.0,
		gridfin_height=7.0,
		hole_num_x=5,
		gridfin_x=2,
		hole_num_y=4,
		gridfin_y=2,
		hole_chamfer_size=2.0,
		hole_circle=True,
		increase_copies=1,
		increase_amount=0.5,
		hole_max_size=10.0,
		hole_min_size=0.5,
		increase_loop_after=20,
		edge_padding=0.0,
		x_padding=6.0,
		y_padding=6.0,
		y_uppies=12.0,
		no_lip=True,
		no_lip_upper_size=2.0,
		no_lip_fillet_size=0.3
	))

	holders.append(Holder(
		name="aa battery holder",
		version=SemVer(1, 0, 2),

		hole_size_flat=14.4,
		hole_depth=15.0,
		fill_mm=18.0,
		gridfin_height=7.0,
		hole_num_x=4,
		gridfin_x=2,
		hole_num_y=2,
		gridfin_y=1,
		hole_chamfer_size=2.35,
		hole_circle=True,
		increase_copies=1,
		increase_amount=0,
		hole_max_size=10000,
		hole_min_size=0,
		increase_loop_after=20,
		edge_padding=0.0,
		x_padding=2.0,
		y_padding=1,
		y_uppies=0,
		no_lip=True,
		no_lip_upper_size=2.0,
		no_lip_fillet_size=0.3
	))

	holders.append(Holder(
		name="aaa battery holder",
		version=SemVer(1, 0, 0),

		hole_size_flat=10.225,
		hole_depth=15.0,
		fill_mm=18.0,
		gridfin_height=7.0,
		hole_num_x=4,
		gridfin_x=2,
		hole_num_y=2,
		gridfin_y=1,
		hole_chamfer_size=4.5,
		hole_circle=True,
		increase_copies=1,
		increase_amount=0,
		hole_max_size=10000,
		hole_min_size=0,
		increase_loop_after=20,
		edge_padding=0.0,
		x_padding=3.5,
		y_padding=3,
		y_uppies=0,
		no_lip=True,
		no_lip_upper_size=2.0,
		no_lip_fillet_size=0.3
	))

	holders.append(Holder(
		name="chapstick holder",
		version=SemVer(1, 0, 1),

		hole_size_flat=15.60,
		hole_depth=15.0,
		fill_mm=18.0,
		gridfin_height=7.0,
		hole_num_x=4,
		gridfin_x=2,
		hole_num_y=2,
		gridfin_y=1,
		hole_chamfer_size=1.7,
		hole_circle=True,
		increase_copies=1,
		increase_amount=0,
		hole_max_size=10000,
		hole_min_size=0,
		increase_loop_after=1,
		edge_padding=0.0,
		x_padding=0.5,
		y_padding=0.3,
		y_uppies=0,
		no_lip=True,
		no_lip_upper_size=2.0,
		no_lip_fillet_size=0.3
	))


	try:
		script_dir = Path(__file__).resolve().parent
		out_dir = script_dir.joinpath("out")
		out_dir.mkdir(parents=True, exist_ok=True)
	except NameError:
		print("can't get script path")
		out_dir = doesnt_exist_script_dir

		if __name__ == "__main__":
			exit(1)
		# script_dir = Path.cwd()


	loop_output(out_dir, holders)



main()
