from dataclasses import dataclass, field
import cadquery as cq
from cadquery import exporters
from pathlib import Path # noqa


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
	charge_slot: bool = True

	wallet_len: float = 51.3 + 0.4
	wallet_width: float = 33.65
	wallet_depth: float = 50
	wallet_x_mov: float = 0
	usb_size: float = 15


	# Fill value (for 20mm use 7, for 50mm use 18; using 18)
	fill_mm: float = 18.0

	# Grid fin parameters
	gridfin_height: float = 7.0
	hole_num_x: int = 5
	gridfin_x: int = 2
	hole_num_y: int = 4
	gridfin_y: int = 2

	# Chamfer size: for 20mm use 1.1; for 50mm use 2 (using 2)
	hole_chamfer_size_x: float = 1.0
	hole_chamfer_size_y: float = 2.5
	hole_chamfer_size_z: float = 2.5


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


hole_margin_small = 0.0
hole_margin_normal = 0.0


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



def make_basic_box(fill_mm, gridfin_x, gridfin_y, gridfin_height, gf_hi_size, no_lip):
	sr = to_solid_ratio(fill_mm, gf_hi_size, gridfin_height)

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
	return bh


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



def to_solid_ratio(n, gf_hi_size, gridfin_height):
	return n / (gf_hi_size * gridfin_height)
	# return ((n / ((gf_hi_size-(0.9623333333+1.2)) * height)) * -1) + 1
	# return ((n / ((gf_hi_size) * height)) * -1) + 1
	# return ((n / (gf_size_t_bot * height)) * -1) + 1

def make_holder(holder):
	fill_mm = holder.fill_mm
	gridfin_height = holder.gridfin_height
	hole_num_x = holder.hole_num_x
	gridfin_x = holder.gridfin_x
	hole_num_y = holder.hole_num_y
	gridfin_y = holder.gridfin_y
	hole_chamfer_size = holder.hole_chamfer_size_y
	edge_padding = holder.edge_padding
	x_padding = holder.x_padding
	y_padding = holder.y_padding
	no_lip = holder.no_lip
	no_lip_upper_size = holder.no_lip_upper_size
	no_lip_fillet_size = holder.no_lip_fillet_size




	gf_hi_size = 7
	gf_horizontal_size = 42
	gf_padding = 2.95
	gf_lip_size = 3.8  # this is exactly correct
	hex_short_to_long = 1.1547




	bh = make_basic_box(fill_mm, gridfin_x, gridfin_y, gridfin_height, gf_hi_size, no_lip)

	# bh = cqg.
	# make the base
	result = (
		bh.cq_obj
		# .faces(">Z")
		# .workplane()
	)

	size_wid = gf_horizontal_size * gridfin_x
	size_dep = gf_horizontal_size * gridfin_y


	z_face_flat = "-2"

	# move_x = (((size_wid)) / (hole_num_x+1))

	x_full_padding = gf_padding + x_padding
	y_full_padding = gf_padding + y_padding

	result_pre_hold_edges = (
		result
		.faces(">Z[-2]")
		.edges()
	)

	result_pre_all_edges = (
		result
		.faces()
		.edges()
	)
	# show_object(result_pre_hold_edges)





	result = result.faces(f">Z[{z_face_flat}]").workplane(
		).transformed(rotate=(0, 0, 0)
		).moveTo(
		(
			holder.wallet_x_mov
		), 0+(
			0
		)).rect(
			holder.wallet_width,
			holder.wallet_len,
		).cutBlind(
			-(holder.wallet_depth)
	)




	# if hole_chamfer_size > 0:
	#
	# 	result = (
	# 		result
	# 		.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
	# 		# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
	# 		.edges()
	# 		.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
	# 		# # ignore 4 longest edges, should always be the edge of the box
	# 		# .sort(lambda edge: edge.Length())[::-1][4:]
	# 		#
	# 		# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
	# 		# # .filter(lambda edge: edge.isCircle())
	# 		.chamfer(holder.hole_chamfer_size_wallet)
	# 	)







	sd_wid = 24 + 0.4
	sd_y = 2.1 + 0.4
	sd_dep = 10 + holder.hole_chamfer_size_y

	# card_size_x = 85.60 + 0.4 # credit card
	card_size_x = 92.0 + 0.4 # social security card
	card_size_dep = 20
	card_size_y = 2.5








	if hole_chamfer_size > 0:

		# result = (
		# 	result
		# 	.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
		# 	# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
		# 	.edges()
		# 	.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
		# 	# .edges("<Y[1]")
		# 	# # ignore 4 longest edges, should always be the edge of the box
		# 	# .sort(lambda edge: edge.Length())[::-1][4:]
		# 	#
		# 	# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
		# 	# # .filter(lambda edge: edge.isCircle())
		# 	.chamfer(holder.hole_chamfer_size_y)
		# )



		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
			.edges()
			.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
			.edges("<Y")
			# # ignore 4 longest edges, should always be the edge of the box
			# .sort(lambda edge: edge.Length())[::-1][4:]
			#
			# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
			# # .filter(lambda edge: edge.isCircle())
			.chamfer(holder.hole_chamfer_size_y, holder.hole_chamfer_size_z)
		)
		# return result, holder

		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
			.edges()
			.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
			.edges(">Y")
			# # ignore 4 longest edges, should always be the edge of the box
			# .sort(lambda edge: edge.Length())[::-1][4:]
			#
			# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
			# # .filter(lambda edge: edge.isCircle())
			.chamfer(holder.hole_chamfer_size_y, holder.hole_chamfer_size_z)
		)
		# return result, holder

		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
			.edges()
			.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
			.edges("<X")
			# # ignore 4 longest edges, should always be the edge of the box
			# .sort(lambda edge: edge.Length())[::-1][4:]
			#
			# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
			# # .filter(lambda edge: edge.isCircle())
			.chamfer(holder.hole_chamfer_size_x, holder.hole_chamfer_size_z)
		)

		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
			.edges()
			.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
			.edges(">X")
			# # ignore 4 longest edges, should always be the edge of the box
			# .sort(lambda edge: edge.Length())[::-1][4:]
			#
			# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
			# # .filter(lambda edge: edge.isCircle())
			.chamfer(holder.hole_chamfer_size_x, holder.hole_chamfer_size_z)
		)
		# return result, holder




	edges = (
		result
		.faces()  # Select the bottom face of the hexagonal holes
		.edges()
		.filter(lambda edge: edge not in result_pre_all_edges.objects)  # Exclude specific edges
		.edges("|Z")
	)

	edges2 = (
		result
		.faces()  # Select the bottom face of the hexagonal holes
		.edges()
		.filter(lambda edge: edge not in result_pre_all_edges.objects)  # Exclude specific edges
		.edges("<<Y[5] or >>Y[5]")
		.edges("<<Z[1]")
	)

	result = (
		result
		.faces()  # Select the bottom face of the hexagonal holes
		.edges()
		.filter(lambda edge: edge not in result_pre_all_edges.objects)  # Exclude specific edges
		.filter(lambda edge: (edge in edges.objects) or (edge in edges2.objects))  # Exclude specific edges
		# .edges("|Z")
		# .edges("<<Y[5] or >>Y[5]")
		# .edges("<<Z[1]")
		.fillet(7)
	)
	# return result, holder


	if no_lip:
		cut_size = no_lip_upper_size
		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			.workplane(offset=no_lip_upper_size)
			.rect(size_wid * 2, size_dep * 2)  # Create a rectangle of width and depth

			.cutBlind((bh.height))
		)

		result = (
			result
			.faces(">Z")  # Select the bottom face of the hexagonal holes
			.edges("%LINE")   # Select all straight edges
			.fillet(no_lip_fillet_size)
		)


	result_pre_all_edges = (
		result
		.faces()
		.edges()
	)

	result = result.faces(f">Z[{z_face_flat}]").workplane(
		).transformed(offset=(0, 0, holder.no_lip_upper_size + 5), rotate=(0, 0, 0)
		).moveTo(
		(
			holder.wallet_x_mov
		), 0+(
			30
		)).rect(
			holder.usb_size,
			40,
		).cutBlind(
			-(holder.wallet_depth + holder.no_lip_upper_size + 5)
	)


	if holder.charge_slot:
		result = (
			result
			.faces()  # Select the bottom face of the hexagonal holes
			.edges()
			.filter(lambda edge: edge not in result_pre_all_edges.objects)  # Exclude specific edges
			# .edges("|Z")
			# .edges("<<Y[5] or >>Y[5]")
			.edges("(<<Z[9]) or <<Z[8] or << Z[7] or <<Z[5] or (<<Z[4] and |Y)")
			.fillet(0.4)
		)

	return result, holder


def main():
	mf100 = Holder(
		name="wolfbox mf100 holder",
		version=SemVer(1, 0, 1),
		gridfin_x=1,
		gridfin_y=2,
		gridfin_height=20,
		no_lip=True,
		no_lip_upper_size=1.25,
		hole_chamfer_size_x=2.9,
		hole_chamfer_size_y=10,
		hole_chamfer_size_z=10,
		wallet_depth=-1,
		fill_mm=-1,
	)

	mf100.wallet_depth = 43 + mf100.hole_chamfer_size_z
	mf100.fill_mm = mf100.wallet_depth + 5



	try:
		script_dir = Path(__file__).resolve().parent
		out_dir = script_dir.joinpath("out")
		out_dir.mkdir(parents=True, exist_ok=True)
	except NameError:
		print("can't get script path")
		out_dir = doesnt_exist_script_dir

		if __name__ == "__main__":
			exit(1)


	holder_in = mf100
	result, holder = make_holder(holder=holder_in)
	show_object(result, name=holder.name+" v"+str(holder.version))

	if __name__ == "__main__" and (out_dir != doesnt_exist_script_dir):
		exporters.export(
			w=result,
			fname=str(out_dir.joinpath(
				f"{holder.name} v{str(holder.version)}.stl"
			)),
			tolerance=1e-5
		)


main()
