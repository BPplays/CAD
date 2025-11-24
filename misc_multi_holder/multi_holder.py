from __future__ import annotations
from dataclasses import dataclass, field
from cadquery import exporters
from pathlib import Path # noqa
from typing import Dict, Union

hole_margin_small = 0.6
hole_margin_normal = 0.4


class SemVer:
	def __init__(self, major: int, minor: int, patch: int):
		self.major = major
		self.minor = minor
		self.patch = patch

	def __repr__(self):
		return f"{self.major}.{self.minor}.{self.patch}"

Number = Union[int, float]



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
from typing import Dict, Union, Callable, Any, Optional
if 'show_object' not in globals():
	def show_object(*args, **kwargs):
		pass
# pylint: skip-file

def to_range(a, range_start, range_end):
    if range_end == range_start:
        return 0
    t = (a - range_start) / (range_end - range_start)
    return max(0, min(1, t))

def interp(a, b, t):
    t = max(min(t, 1), 0)

    a_mix = a * (1 - t)
    b_mix = b * t

    return a_mix + b_mix

class HoleShape:
	# def __new__(cls, *args, **kwargs):
	# 	# called before __init__; create instance and set per-instance empty dict
	# 	self = super().__new__(cls)
	# 	self.sizes: Dict[str, float] = {}  # initialized _pre-__init__
	# 	return self

	def __init__(
		self,
		type_: str,
		sizes: Optional[Dict[str, Number]] = None,
	):
		self.type_ = type_
		self.sizes = sizes
		self.sizes: Dict[str, float] = {k: float(v) for k, v in (sizes or {}).items()}


	def SetSize(self, *args, **kwargs) -> None:
		raise NotImplementedError

	def GetSize(self):
		raise NotImplementedError

	def GetXY(self):
		raise NotImplementedError

	def MakeCut(
		self,
		workplane,
		holder: Holder,
		hole_depth: float,
		i_x: int,
		i_y: int,
		total_loops: int,
	):
		raise NotImplementedError


	# helper to merge keys and produce new sizes dict
	def _apply_op(
		self,
		other: Union[Dict[str, Number], Number],
		op: str,
	) -> Dict[str, float]:
		"""Return a new sizes dict after applying operation.
		op in {"add", "sub", "mul", "div"}.
		If other is a scalar apply to every key.
		If other is a dict: for add/sub missing keys -> 0; for mul/div missing keys -> 1.
		Keys present only in `other` are included in the result.
		"""
		if isinstance(other, (int, float)):
			# scalar path
			if op == "add":
				return {k: float(v + other) for k, v in self.sizes.items()}
			if op == "sub":
				return {k: float(v - other) for k, v in self.sizes.items()}
			if op == "mul":
				return {k: float(v * other) for k, v in self.sizes.items()}
			if op == "div":
				if other == 0:
					raise ValueError("Division by zero (scalar).")
				return {k: float(v / other) for k, v in self.sizes.items()}
			raise ValueError(f"Unknown op {op}")

		# other is a dict path
		other_dict = {k: float(v) for k, v in other.items()}
		# union of keys
		all_keys = set(self.sizes.keys()) | set(other_dict.keys())
		result: Dict[str, float] = {}

		for k in all_keys:
			a = float(self.sizes.get(k, 0.0))
			b = float(other_dict.get(k, 0.0))

			if op == "add":
				# missing other treated as 0 by using .get above
				result[k] = a + b
			elif op == "sub":
				# missing other treated as 0
				result[k] = a - b
			elif op == "mul":
				# missing other should be treated as 1 (so adjust b)
				b = other_dict.get(k, 1.0)
				result[k] = a * float(b)
			elif op == "div":
				b = other_dict.get(k, 1.0)
				if b == 0:
					raise ValueError(f"Division by zero for key '{k}'")
				# if a missing previously we used 0.0 -> 0 / b == 0
				result[k] = a / float(b)
			else:
				raise ValueError(f"Unknown op {op}")

		return result

	# public arithmetic methods
	def Add(
		self,
		other: Union[Dict[str, Number], Number],
		in_place: bool = True,
	) -> "HoleShape":
		new_sizes = self._apply_op(other, "add")
		if in_place:
			self.sizes = new_sizes
			return self
		return HoleShape(self.type, new_sizes)

	def Subtract(
		self,
		other: Union[Dict[str, Number], Number],
		in_place: bool = True,
	) -> "HoleShape":
		new_sizes = self._apply_op(other, "sub")
		if in_place:
			self.sizes = new_sizes
			return self
		return HoleShape(self.type, new_sizes)

	def Mult(
		self,
		other: Union[Dict[str, Number], Number],
		in_place: bool = True,
	) -> "HoleShape":
		new_sizes = self._apply_op(other, "mul")
		if in_place:
			self.sizes = new_sizes
			return self
		return HoleShape(self.type, new_sizes)

	def Div(
		self,
		other: Union[Dict[str, Number], Number],
		in_place: bool = True,
	) -> "HoleShape":
		new_sizes = self._apply_op(other, "div")
		if in_place:
			self.sizes = new_sizes
			return self
		return HoleShape(self.type, new_sizes)

class Hexagon(HoleShape):
	def __init__(
		self,
		flat_side_size: float,
	):
		super().__init__(type_="hexagon")
		self.SetSize(flat_side_size)

	def SetSize(self, flat_side_size: float):
		self.sizes["flat_side_size"] = flat_side_size

	def GetSize(self) -> (float, float):
		flat_side_size = self.sizes["flat_side_size"]

		hex_short_to_long = 1.1547
		pointy_side_size = flat_side_size * hex_short_to_long
		return flat_side_size, pointy_side_size

	def GetXY(self, direction: str):
		hole_size = 0
		hole_size_flat, hole_size_pointy = self.GetSize()
		if direction == "x":
			hole_size = hole_size_pointy

		if direction == "y":
			hole_size = hole_size_flat
		return hole_size

	def MakeCut(
		self,
		workplane,
		holder: Holder,
		hole_depth: float,
		i_x: int,
		i_y: int,
		total_loops: int,
	):
		hole_size_flat, hole_size_pointy = self.GetSize()
		result = workplane.polygon(
			6,
			holder.size_func(hole_size_pointy, holder, i_x, i_y, total_loops),
		).cutBlind(
			-(hole_depth)
		)
		return result


class Circle(HoleShape):
	def __init__(
		self,
		diameter: float,
	):
		super().__init__(type_="circle")
		self.SetSize(diameter)

	def SetSize(self, diameter: float):
		self.sizes["diameter"] = diameter

	def GetSize(self) -> (float):
		return self.sizes["diameter"]

	def GetXY(self, direction: str):
		hole_size = 0
		diameter = self.GetSize()
		hole_size = diameter
		return hole_size

	def MakeCut(
		self,
		workplane,
		holder: Holder,
		hole_depth: float,
		i_x: int,
		i_y: int,
		total_loops: int,
	):
		diameter = self.GetSize()
		result = workplane.circle(
			holder.size_func(diameter, holder, i_x, i_y, total_loops) / 2,
		).cutBlind(
			-(hole_depth)
		)
		return result


class Rect(HoleShape):
	def __init__(
		self,
		x: float,
		y: float,
	):
		super().__init__(type_="rect")
		self.SetSize(x, y)

	def SetSize(self, x: float, y: float):
		self.sizes["x"] = x
		self.sizes["y"] = y

	def GetSize(self) -> (float, float):
		return self.sizes["x"], self.sizes["y"]

	def GetXY(self, direction: str):
		hole_size = 0

		x, y = self.GetSize()

		if direction == "x":
			hole_size = x

		if direction == "y":
			hole_size = y

		return hole_size

	def MakeCut(
		self,
		workplane,
		holder: Holder,
		hole_depth: float,
		i_x: int,
		i_y: int,
		total_loops: int,
	):
		x, y = self.GetSize()
		result = workplane.rect(
			holder.size_func(x, holder, i_x, i_y, total_loops),
			holder.size_func(y, holder, i_x, i_y, total_loops),
		).cutBlind(
			-(hole_depth)
		)
		return result

class RectDouble(HoleShape):
	def __init__(
		self,
		x: float,
		y: float,

		x2: float,
		y2: float,
	):
		super().__init__(type_="rect_double")
		self.SetSize(x, y, x2, y2)

	def SetSize(self, x: float, y: float, x2: float, y2: float):
		self.sizes["x"] = x
		self.sizes["y"] = y

		self.sizes["x2"] = x2
		self.sizes["y2"] = y2

	def GetSize(self) -> (float, float):
		return self.sizes["x"], self.sizes["y"], self.sizes["x2"], self.sizes["y2"]

	def GetXY(self, direction: str):
		hole_size = 0

		x, y, x2, y2 = self.GetSize()

		if direction == "x":
			hole_size = max(x, x2)

		if direction == "y":
			hole_size = max(y, y2)

		return hole_size

	def MakeCut(
		self,
		workplane,
		holder: Holder,
		hole_depth: float,
		i_x: int,
		i_y: int,
		total_loops: int,
	):
		x, y, x2, y2 = self.GetSize()
		result = workplane.rect(
			holder.size_func(x, holder, i_x, i_y, total_loops),
			holder.size_func(y, holder, i_x, i_y, total_loops),
		).cutBlind(
			-(hole_depth)
		)

		result2 = workplane.rect(
			holder.size_func(x2, holder, i_x, i_y, total_loops),
			holder.size_func(y2, holder, i_x, i_y, total_loops),
		).cutBlind(
			-(hole_depth)
		)

		result = and_models([result, result2])

		return result



def size_increase_margin(
	size: float,
	_ = None,
	__ = None,
	___ = None,
	____ = None,
) -> float:
	smallness = to_range(size, 2.25, 1.6)
	margin = interp(hole_margin_normal, hole_margin_small, smallness)

	return size + margin


def size_indentity(
	size: float,
	_,
	__,
	___,
	____,
) -> float:
	return size

def size_default_increase(
	size: float,
	_,
	__,
	___,
	____,
) -> float:
	return size_increase_margin(size, _, __, ___, ____)


class Holder_Model:
	def __init__(
		self,
		holder: Holder,
		model: Any,
	) -> None:
		self.holder = holder
		self.model = model

# @dataclass
class Holder:
	def __init__(
		self,
		name: str = "",
		version: Optional[SemVer] = None,
		hole_shape: Optional[HoleShape] = None,
		hole_shape_max: Optional[HoleShape] = None,
		hole_shape_min: Optional[HoleShape] = None,
		no_margin: bool = False,
		size_func: Optional[Callable[[float, Any, int, int], float]] = None,
		*,
		# primitives (same defaults as your dataclass)
		hole_size_flat: float = 0.5,
		hole_depth: float = 15.0,
		fill_mm: float = 18.0,
		gridfin_height: float = 7.0,
		hole_num_x: int = 5,
		gridfin_x: int = 2,
		hole_num_y: int = 4,
		gridfin_y: int = 2,
		hole_chamfer_size: float = 2.0,
		hole_circle: bool = True,
		increase_copies: int = 1,
		increase_amount: float = 0.5,
		hole_max_size: float = 10.0,
		hole_min_size: float = 0.5,
		increase_loop_after: int = 20,
		edge_padding: float = 0.0,
		x_padding: float = 6.0,
		y_padding: float = 6.0,
		y_uppies: float = 12.0,
		no_lip: bool = True,
		no_lip_upper_size: float = 2.0,
		no_lip_fillet_size: float = 0.3,
	) -> None:
		# simple fields
		self.name = name
		self.version = version if version is not None else SemVer(1, 0, 0)

		# Hole shapes: ensure valid instances
		self.hole_shape = hole_shape if hole_shape is not None else Rect(1, 1)
		self.hole_shape_max = (
			hole_shape_max if hole_shape_max is not None else Rect(1, 1)
		)

		self.hole_shape_min = (
			hole_shape_min if hole_shape_min is not None else Rect(1, 1)
		)

		# size function
		self.size_func = size_func if size_func is not None else size_default_increase

		# primitive defaults
		self.hole_size_flat = float(hole_size_flat)
		self.hole_depth = float(hole_depth)
		self.fill_mm = float(fill_mm)
		self.gridfin_height = float(gridfin_height)
		self.hole_num_x = int(hole_num_x)
		self.gridfin_x = int(gridfin_x)
		self.hole_num_y = int(hole_num_y)
		self.gridfin_y = int(gridfin_y)
		self.hole_chamfer_size = float(hole_chamfer_size)
		self.hole_circle = bool(hole_circle)
		self.increase_copies = int(increase_copies)
		self.increase_amount = float(increase_amount)
		self.hole_max_size = float(hole_max_size)
		self.hole_min_size = float(hole_min_size)
		self.increase_loop_after = int(increase_loop_after)
		self.edge_padding = float(edge_padding)
		self.x_padding = float(x_padding)
		self.y_padding = float(y_padding)
		self.y_uppies = float(y_uppies)
		self.no_lip = bool(no_lip)
		self.no_lip_upper_size = float(no_lip_upper_size)
		self.no_lip_fillet_size = float(no_lip_fillet_size)

	def __post_init__(self) -> None:
		# Ensure version is always a SemVer instance
		if self.version is None:
			self.version = SemVer(1, 0, 0)

		# Ensure hole_shape and hole_shape_limit are always HoleShape instances
		if self.hole_shape is None:
			self.hole_shape = Rect(1, 1)
		if self.hole_shape_limit is None:
			self.hole_shape_limit = Rect(1, 1)

		# Ensure size_func is a callable
		if self.size_func is None:
			self.size_func = size_default_increase

	def __repr__(self) -> str:
		return (
			f"Holder(name={self.name!r}, version={self.version!r}, "
			f"hole_shape={self.hole_shape!r}, hole_size_flat={self.hole_size_flat})"
		)



def size_increase_drill(
	size: float,
	holder: "Holder",
	i_x: int,
	i_y: int,
	total_loops,
) -> float:
	hole_size_cir = 0
	hole_size_cir_base = size
	total_loops += 1

	max_diameter = holder.hole_shape_max.GetSize()
	min_diameter = holder.hole_shape_min.GetSize()

	print("xy", i_x, i_y)

	for loop_index in range(total_loops):
		if loop_index % holder.increase_loop_after == 0:
			hole_size_cir_base = size

		if hole_size_cir_base > holder.hole_max_size:
			hole_size_cir = holder.hole_max_size
		elif hole_size_cir_base < holder.hole_min_size:
			hole_size_cir = holder.hole_min_size
		else:
			hole_size_cir = hole_size_cir_base


		hole_size_cir = max(hole_size_cir, min_diameter)
		hole_size_cir = min(hole_size_cir, max_diameter)

		hole_size_cir = size_increase_margin(hole_size_cir)


		if loop_index % holder.increase_copies == 0:
			hole_size_cir_base += holder.increase_amount

	print("loop", total_loops, "radius", hole_size_cir)
	return hole_size_cir



def get_start(
	shape: HoleShape,
	direction: str,
	size,
	xy_full_padding,
	num: int,
	uppies=0,
):
	hole_size = 0
	start = 0

	if num <= 1:
		return start


	hole_size = shape.GetXY(direction)


	if direction == "x":
		start_hor = (-(size) / 2) + (hole_size / 2) + xy_full_padding
		start = start_hor

	if direction == "y":
		start_virt = (-(size-uppies) / 2) + (hole_size / 2) + xy_full_padding
		start = start_virt

	return start

def get_move_xy(
	shape: HoleShape,
	direction: str,
	size_dw,
	xy_full_padding,
	hole_num,
	uppies=0,
):
	hole_size = 0

	hole_size = shape.GetXY(direction)

	if hole_num > 1:
		move = (((size_dw) - ((2 * xy_full_padding) + (uppies / 2)) - hole_size) / (hole_num - 1))
	else:
		move = (((size_dw) - ((2 * xy_full_padding) + (uppies / 2)) - hole_size))

	return move


def make_cut(
	shape: HoleShape,
	workplane,
	holder: Holder,
	hole_depth: float,
	i_x: int,
	i_y: int,
	total_loops: int,
):

	if shape.type_ == "circle":
		diameter = shape.GetSize()
		result = workplane.circle(
			holder.size_func(diameter, holder, i_x, i_y, total_loops) / 2,
		).cutBlind(
			-(hole_depth)
		)

	if shape.type_ == "hexagon":
		hole_size_flat, hole_size_pointy = shape.GetSize()
		result = workplane.polygon(
			6,
			holder.size_func(hole_size_pointy, holder, i_x, i_y, total_loops),
		).cutBlind(
			-(hole_depth)
		)

	if shape.type_ == "rect":
		x, y = shape.GetSize()
		result = workplane.rect(
			holder.size_func(x, holder, i_x, i_y, total_loops),
			holder.size_func(y, holder, i_x, i_y, total_loops),
		).cutBlind(
			-(hole_depth)
		)

	return result



def make_hole(
	holder: Holder,
	result,
	i: int,
	i2: int,
	start_hor,
	start_virt,
	move_x: float,
	move_y: float,
	z_face_flat,
	total_loops: int,
):


	wp = result.faces(f">Z[{z_face_flat}]").workplane().moveTo(
		(
			start_hor+(i*move_x)
		), start_virt+(
			i2*move_y
		))

	result = holder.hole_shape.MakeCut(
		workplane=wp,
		holder=holder,
		hole_depth=holder.hole_depth,
		i_x=i,
		i_y=i2,
		total_loops=total_loops
	)

	# show_object(wp)
	# return wp
	# result = make_cut(
	# 	shape=shape,
	# 	workplane=wp,
	# 	holder=holder,
	# 	hole_depth=holder.hole_depth,
	# 	i_x=i,
	# 	i_y=i2,
	# 	total_loops=total_loops
	# )

	return result


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


	start_hor = get_start(
		holder.hole_shape,
		"x",
		size_wid,
		x_full_padding,
		holder.hole_num_x,
	)

	start_virt = get_start(
		holder.hole_shape,
		"y",
		size_dep,
		y_full_padding,
		holder.hole_num_y,
		y_uppies,
	)


	result_pre_hold_edges = (
		result
		.faces(">Z[-2]")
		.edges()
	)
	# show_object(result_pre_hold_edges)



	move_x = get_move_xy(
		holder.hole_shape,
		"x",
		size_wid,
		x_full_padding,
		hole_num_x
	)
	move_y = get_move_xy(
		holder.hole_shape,
		"y",
		size_dep,
		y_full_padding,
		hole_num_y,
		y_uppies
	)


	# hole_size_cir = hole_size_flat

	total_loops = 0
	for i2 in range(hole_num_y):
		for i in range(hole_num_x):
			result = make_hole(
				holder=holder,
				result=result,
				i=i,
				i2=i2,
				start_hor=start_hor,
				start_virt=start_virt,
				move_x=move_x,
				move_y=move_y,
				z_face_flat=z_face_flat,
				total_loops=total_loops,
			)
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




def and_models(models):
	main_result = None

	for model in models:
		if main_result is None:
			main_result = model
		else:
			main_result = main_result.intersect(model)

	return main_result

def and_holders(holders):
	main_result = None
	main_holder = None

	for holder in holders:
		result, _ = make_holder(holder=holder)
		if main_result is None:
			main_result = result
			main_holder = holder
		else:
			main_result = main_result.intersect(result)

	return Holder_Model(main_holder, main_result)


def loop_output(out_dir, holders, models, filter = ""):

	for holder in holders:
		if not (filter == holder.name or filter == ""):
			continue

		result, holder = make_holder(holder=holder)
		models.append(Holder_Model(holder, result))

	for model in models:
		if not (filter == model.holder.name or filter == ""):
			continue

		show_object(
			model.model,
			name=f"{model.holder.name} v{str(model.holder.version)}"
		)

		if not (__name__ == "__main__" and (out_dir != doesnt_exist_script_dir)):
			continue

		exporters.export(
			model.model,
			str(out_dir.joinpath(
				f"{model.holder.name} v{str(model.holder.version)}.step"
			))
		)



def main():
	holders = []

	holders.append(Holder(
		name="drill bit holder",
		version=SemVer(1, 0, 0),
		hole_shape=Circle(0.5),
		hole_shape_max=Circle(10.0),
		hole_shape_min=Circle(0.01),
		size_func=size_increase_drill,

		hole_depth=15.0,
		fill_mm=18.0,
		gridfin_height=7.0,
		hole_num_x=5,
		gridfin_x=2,
		hole_num_y=4,
		gridfin_y=2,
		hole_chamfer_size=2.0,
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
		hole_shape=Circle(14.4),
		hole_shape_max=Circle(99999999999),
		hole_shape_min=Circle(0.01),

		hole_size_flat=14.4,
		hole_depth=15.0,
		fill_mm=18.0,
		gridfin_height=7.0,
		hole_num_x=4,
		gridfin_x=2,
		hole_num_y=2,
		gridfin_y=1,
		hole_chamfer_size=2.225,
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
		name="8 aaa battery holder",
		version=SemVer(1, 0, 1),
		hole_shape=Circle(10.35),
		hole_shape_max=Circle(9999999),
		hole_shape_min=Circle(0.01),

		hole_depth=15.0,
		fill_mm=18.0,
		gridfin_height=7.0,
		hole_num_x=4,
		gridfin_x=2,
		hole_num_y=2,
		gridfin_y=1,
		hole_chamfer_size=4,
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
		name="10 aaa battery holder",
		version=SemVer(1, 0, 1),
		hole_shape=Circle(10.35),
		hole_shape_max=Circle(9999999),
		hole_shape_min=Circle(0.01),

		hole_depth=15.0,
		fill_mm=18.0,
		gridfin_height=7.0,
		hole_num_x=5,
		gridfin_x=2,
		hole_num_y=2,
		gridfin_y=1,
		hole_chamfer_size=2.5,
		hole_circle=True,
		increase_copies=1,
		increase_amount=0,
		hole_max_size=10000,
		hole_min_size=0,
		increase_loop_after=20,
		edge_padding=0.0,
		x_padding=2.2,
		y_padding=3.1,
		y_uppies=0,
		no_lip=True,
		no_lip_upper_size=2.0,
		no_lip_fillet_size=0.3
	))

	holders.append(Holder(
		name="chapstick holder",
		version=SemVer(1, 0, 1),
		hole_shape=Circle(15.60),
		hole_shape_max=Circle(99999999),
		hole_shape_min=Circle(0.01),

		hole_size_flat=15.60,
		hole_depth=15.0,
		fill_mm=18.0,
		gridfin_height=7.0,
		hole_num_x=4,
		gridfin_x=2,
		hole_num_y=2,
		gridfin_y=1,
		hole_chamfer_size=1.5,
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


	holders.append(Holder(
		name="9v battery holder",
		version=SemVer(1, 0, 1),
		hole_shape=Rect(26, 17),
		hole_shape_max=Rect(999, 999),
		# hole_shape_min=Circle(0.01),
		# size_func=size_increase_drill,

		hole_depth=17.0,
		fill_mm=20.0,
		gridfin_height=7.0,
		hole_num_x=5,
		gridfin_x=4,
		hole_num_y=2,
		gridfin_y=2,
		hole_chamfer_size=3,
		increase_copies=1,
		increase_amount=0.5,
		increase_loop_after=20,
		edge_padding=0.0,
		x_padding=3.0,
		y_padding=4.5,
		y_uppies=13.0,
		no_lip=True,
		no_lip_upper_size=2.0,
		no_lip_fillet_size=0.3
	))

	holders.append(Holder(
		name="nozzle holder",
		version=SemVer(1, 0, 0),
		hole_shape=Circle(5.81),
		hole_shape_max=Circle(9999.0),
		hole_shape_min=Circle(0.01),

		hole_size_flat=15.60,
		hole_depth=3.10 + 1,
		fill_mm=5,
		gridfin_height=3,
		hole_num_x=4,
		gridfin_x=2,
		hole_num_y=2,
		gridfin_y=1,
		hole_chamfer_size=1,
		increase_copies=1,
		increase_amount=0,
		hole_max_size=10000,
		hole_min_size=0,
		increase_loop_after=1,
		x_padding=10,
		y_padding=6,
		y_uppies=9.5,
		no_lip=False,
		no_lip_upper_size=2.0,
		no_lip_fillet_size=0.3
	))

	holders.append(Holder(
		name="d battery holder",
		version=SemVer(1, 0, 0),
		hole_shape=Circle(32.36),
		hole_shape_max=Circle(9999999),
		hole_shape_min=Circle(0.01),

		hole_depth=17.0,
		fill_mm=20.0,
		gridfin_height=7.0,
		hole_num_x=2,
		gridfin_x=2,
		hole_num_y=2,
		gridfin_y=2,
		hole_chamfer_size=3.98,
		hole_circle=True,
		increase_copies=1,
		increase_amount=0,
		hole_max_size=10000,
		hole_min_size=0,
		increase_loop_after=20,
		edge_padding=0.0,
		x_padding=2.5,
		y_padding=2.5,
		y_uppies=0,
		no_lip=True,
		no_lip_upper_size=2.0,
		no_lip_fillet_size=0.3
	))


	bosch_holders = []
	bosch_holders.append(Holder(
		name="bosch glm165-40 with aaa battery holder",
		version=SemVer(1, 0, 1),
		hole_shape=Rect(41.25, 25),
		hole_shape_max=Circle(9999999),
		hole_shape_min=Circle(0.01),

		hole_depth=30,
		fill_mm=35,
		gridfin_height=7.0,
		hole_num_x=1,
		gridfin_x=2,
		hole_num_y=1,
		gridfin_y=1,
		hole_chamfer_size=5,
		increase_copies=1,
		increase_amount=0,
		hole_max_size=10000,
		hole_min_size=0,
		increase_loop_after=20,
		edge_padding=0.0,
		x_padding=2.5,
		y_padding=2.5,
		y_uppies=0,
		no_lip=True,
		no_lip_upper_size=2.0,
		no_lip_fillet_size=0.3
	))

	bosch_holders.append(Holder(
		name="bosch aaa battery holder",
		version=bosch_holders[0].version,
		hole_shape=Circle(10.35),
		hole_shape_max=Circle(9999999),
		hole_shape_min=Circle(0.01),

		hole_depth=15.0,
		fill_mm=bosch_holders[0].fill_mm,
		gridfin_height=bosch_holders[0].gridfin_height,
		hole_num_x=2,
		gridfin_x=bosch_holders[0].gridfin_x,
		hole_num_y=2,
		gridfin_y=bosch_holders[0].gridfin_y,
		hole_chamfer_size=2.0,
		increase_copies=1,
		increase_amount=0,
		hole_max_size=10000,
		hole_min_size=0,
		increase_loop_after=20,
		edge_padding=0.0,
		x_padding=2.0,
		y_padding=3.1,
		y_uppies=0,
		no_lip=bosch_holders[0].no_lip,
		no_lip_upper_size=bosch_holders[0].no_lip_upper_size,
		no_lip_fillet_size=bosch_holders[0].no_lip_fillet_size
	))


	holders.append(Holder(
		name="vessel tx76u",
		version=SemVer(1, 0, 6),
		hole_shape=RectDouble(
			17.0 + 0.3,
			7.5 + 0.3,
			5.7 + 0.4,
			7.5 + (2 * 2) + 0.4
		),
		size_func=size_indentity,

		hole_shape_max=Circle(9999999),
		hole_shape_min=Circle(0.01),

		hole_depth=26.8,
		fill_mm=30,
		gridfin_height=7.0,
		hole_num_x=1,
		gridfin_x=1,
		hole_num_y=1,
		gridfin_y=1,
		hole_chamfer_size=3.98,
		hole_circle=True,
		increase_copies=1,
		increase_amount=0,
		hole_max_size=10000,
		hole_min_size=0,
		increase_loop_after=20,
		edge_padding=0.0,
		x_padding=2.5,
		y_padding=2.5,
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


	holder_models = []
	holder_models.append(and_holders(bosch_holders))

	loop_output(out_dir, holders, holder_models, "")



main()
