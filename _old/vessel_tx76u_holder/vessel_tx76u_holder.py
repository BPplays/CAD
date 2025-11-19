from dataclasses import dataclass, field
import cadquery as cq


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

	wallet_len: float = 104
	wallet_width: float = 11
	wallet_depth: float = 20
	wallet_x_mov: float = -11


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
	hole_chamfer_size_wallet: float = 3


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


hole_margin_small = 0.6
hole_margin_normal = 0.4

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
			.chamfer(holder.hole_chamfer_size_wallet)
		)




	result_pre_hold_edges = (
		result
		.faces(">Z[-2]")
		.edges()
	)



	sd_wid = 24 + 0.4
	sd_y = 2.1 + 0.4
	sd_dep = 10 + holder.hole_chamfer_size_y

	# card_size_x = 85.60 + 0.4 # credit card
	card_size_x = 92.0 + 0.4 # social security card
	card_size_dep = 20
	card_size_y = 2.5

	result = result.faces(f">Z[{z_face_flat}]").workplane(
		).transformed(rotate=(0, 0, 0)
		).moveTo(
		(
			5.5 + (card_size_y / 2)
		), 0+(
			47.5
		)).rect(
			sd_y,
			sd_wid,
		).cutBlind(
			-(sd_dep)
		)


	result = result.faces(f">Z[{z_face_flat}]").workplane(
		).transformed(rotate=(0, 0, 0)
		).moveTo(
		(
			14.0 + (card_size_y / 2)
		), 0+(
			47.5
		)).rect(
			sd_y,
			sd_wid,
		).cutBlind(
			-(sd_dep)
		)


	# result = result.faces(f">Z[{z_face_flat}]").workplane(
	# 	).transformed(rotate=(0, 0, 0)
	# 	).moveTo(
	# 	(
	# 		-1.5 + (card_size_y / 2)
	# 	), 0+(
	# 		-14
	# 	)).rect(
	# 		card_size_y,
	# 		card_size_x,
	# 	).cutBlind(
	# 		-(card_size_dep)
	# 	)

	result = result.faces(f">Z[{z_face_flat}]").workplane(
		).transformed(rotate=(0, 0, 0)
		).moveTo(
		(
			14.0 + (card_size_y / 2)
		), 0+(
			-13.1
		)).rect(
			card_size_y,
			card_size_x,
		).cutBlind(
			-(card_size_dep)
		)
	result = result.faces(f">Z[{z_face_flat}]").workplane(
		).transformed(rotate=(0, 0, 0)
		).moveTo(
		(
		   5.5 + (card_size_y / 2)
		), 0+(
			-13.1
		)).rect(
			card_size_y,
			card_size_x,
		).cutBlind(
			-(card_size_dep)
		)




	if hole_chamfer_size > 0:

		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
			.edges()
			.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
			.edges("<Y[1]")
			# # ignore 4 longest edges, should always be the edge of the box
			# .sort(lambda edge: edge.Length())[::-1][4:]
			#
			# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
			# # .filter(lambda edge: edge.isCircle())
			.chamfer(holder.hole_chamfer_size_y)
		)
		# return result, holder

		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
			.edges()
			.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
			.edges(">Y[1]")
			# # ignore 4 longest edges, should always be the edge of the box
			# .sort(lambda edge: edge.Length())[::-1][4:]
			#
			# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
			# # .filter(lambda edge: edge.isCircle())
			.chamfer(holder.hole_chamfer_size_y)
		)
		# return result, holder

		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
			.edges()
			.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
			.edges("<X[1]")
			# # ignore 4 longest edges, should always be the edge of the box
			# .sort(lambda edge: edge.Length())[::-1][4:]
			#
			# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
			# # .filter(lambda edge: edge.isCircle())
			.chamfer(holder.hole_chamfer_size_x)
		)

		result = (
			result
			.faces(">Z[-2]")  # Select the bottom face of the hexagonal holes
			# .edges("not(<<X[2] or >>X[2] or <<Y[2] or >>Y[2])")   # Select all straight edges
			.edges()
			.filter(lambda edge: edge not in result_pre_hold_edges.objects)  # Exclude specific edges
			.edges("<X[4]")
			# # ignore 4 longest edges, should always be the edge of the box
			# .sort(lambda edge: edge.Length())[::-1][4:]
			#
			# .edges("not(<<X[0] or >>X[0] or <<Y[0] or >>Y[0])")   # Select all straight edges
			# # .filter(lambda edge: edge.isCircle())
			.chamfer(holder.hole_chamfer_size_x)
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

	return result, holder


def main():
	wallet = Holder(
		name="wallet holder",
		version=SemVer(1, 0, 0),
		gridfin_x=1,
		gridfin_y=3,
		gridfin_height=5,
		no_lip=True,
		no_lip_upper_size=1.25,
		fill_mm=25,
	)



	# Unpack the dataclass instance into the function using asdict
	holder_in = wallet
	result, holder = make_holder(holder=holder_in)
	show_object(result, name=holder.name+" v"+str(holder.version))


main()
