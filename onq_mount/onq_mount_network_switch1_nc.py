"""CadQuery port of the OpenSCAD OnQ tripod/tetrapod mounting plate."""

from dataclasses import dataclass
from math import cos, pi, sin, sqrt

import cadquery as cq


@dataclass
class Parameters:
    # Plate, slats, and pin dimensions (mm)
    plate_height: float = 32.2
    plate_thickness: float = 3.0
    vertical_spacing: float = 25.4
    horizontal_spacing: float = 155.0
    column_offset: float = 12.7
    pin_diameter: float = 6.8
    pin_length: float = 5.4
    hook_thickness: float = 2.5
    slat_thickness: float = 1.0

    # Device mounting holes
    mounting_hole_columns: int = 2
    mounting_hole_rows: int = 1
    mounting_hole_diameter: float = 3.0
    mounting_hole_margin: float = 3.0
    mounting_hole_countersink_diameter: float = 0.0
    mounting_hole_distance: float = 95.0
    mounting_hole_vertical: float = 20.0


def box_at(dx: float, dy: float, dz: float,
           x: float = 0.0, y: float = 0.0, z: float = 0.0) -> cq.Solid:
    """OpenSCAD-style cube: lower corner at (x, y, z), not centered."""
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x, y, z))


def polygon_prism(sides: int, radius: float, height: float,
                  x: float = 0.0, y: float = 0.0, z: float = 0.0) -> cq.Solid:
    """Regular polygon prism with its first vertex on the +X axis."""
    points = [
        (x + radius * cos(2.0 * pi * i / sides),
         y + radius * sin(2.0 * pi * i / sides))
        for i in range(sides)
    ]
    return (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(height)
        .val()
        .translate((0, 0, z))
    )


def fuse_all(parts: list[cq.Shape]) -> cq.Shape:
    """Fuse a collection of touching/overlapping solids into one model."""
    if not parts:
        raise ValueError("Cannot build the mount: there are no solids")

    result = parts[0]
    for part in parts[1:]:
        result = result.fuse(part)
    return result.clean()


def make_pin(p: Parameters, pin_radius: float, pin_width: float) -> cq.Solid:
    """Build one hexagonal pin, including the three OpenSCAD relief cuts."""
    pin = polygon_prism(6, pin_radius, p.pin_length)

    total_z = p.pin_length - p.hook_thickness
    z_cut = (total_z - 3.0 * pin_width / 8.0) * 2.0

    # OpenSCAD transform order:
    # translate(0, 0, z_cut) * rotate(-30, 0, 0) * translate(...) * cube(...)
    slope_cut = box_at(p.pin_diameter, pin_width, total_z)
    slope_cut = (
        slope_cut
        .translate((-p.pin_diameter / 2.0, -pin_width, -total_z))
        .rotate((0, 0, 0), (1, 0, 0), -30)
        .translate((0, 0, z_cut))
    )

    hook_cut = box_at(
        p.pin_diameter,
        p.pin_diameter,
        total_z,
        -pin_radius,
        -p.pin_diameter,
        -total_z + z_cut,
    )

    # translate(-D/2, pin_width/2, pin_length-1) * rotate(45, 0, 0) * cube(...)
    corner_cut = box_at(p.pin_diameter, p.pin_diameter, p.pin_diameter)
    corner_cut = (
        corner_cut
        .rotate((0, 0, 0), (1, 0, 0), 45)
        .translate((-p.pin_diameter / 2.0, pin_width / 2.0, p.pin_length - 1.0))
    )

    return pin.cut(slope_cut).cut(hook_cut).cut(corner_cut).clean()


def pin_pair_parts(p: Parameters, pin: cq.Solid,
                   pin_radius: float, pin_width: float) -> list[cq.Shape]:
    """Return the pin-pair support and its two pins in local coordinates."""
    pair_height = p.vertical_spacing + p.pin_diameter
    support = box_at(
        pair_height,
        pin_width,
        p.plate_thickness + p.slat_thickness,
        0,
        -pin_width / 2.0,
        -p.plate_thickness,
    )

    first_pin = pin.translate((pin_radius, 0, p.slat_thickness))
    second_pin = pin.translate((pin_radius + p.vertical_spacing, 0, p.slat_thickness))
    return [support, first_pin, second_pin]


def plate_parts(p: Parameters, pin_width: float,
                x_offset: float = 0.0) -> list[cq.Shape]:
    """Return the main plate and the raised cross-slats."""
    plate_width = p.horizontal_spacing + pin_width
    parts: list[cq.Shape] = [
        box_at(
            p.plate_height,
            plate_width,
            p.plate_thickness,
            x_offset,
            -pin_width / 2.0,
            -p.plate_thickness,
        )
    ]

    # OpenSCAD: for (y = [17 : 20 : horizontal_spacing - 10])
    y = 17.0
    while y <= p.horizontal_spacing - 10.0 + 1e-9:
        parts.append(
            box_at(p.plate_height, 5.0, p.slat_thickness, x_offset, y, 0.0)
        )
        y += 20.0

    return parts


def mounting_hole_centers(p: Parameters, pin_width: float,
                          plate_offset: float) -> list[tuple[float, float]]:
    """Calculate hole centers using the same grid-centering formula as OpenSCAD."""
    columns = max(0, p.mounting_hole_columns)
    rows = max(0, p.mounting_hole_rows)

    column_spaces = max(columns - 1, 0)
    row_spaces = max(rows - 1, 0)
    grid_width = column_spaces * p.mounting_hole_distance
    grid_height = row_spaces * p.mounting_hole_vertical

    y_first = (
        (p.horizontal_spacing + pin_width) / 2.0
        - pin_width / 2.0
        - grid_width / 2.0
    )
    x_first = plate_offset + p.plate_height / 2.0 - grid_height / 2.0

    return [
        (x_first + row * p.mounting_hole_vertical,
         y_first + col * p.mounting_hole_distance)
        for row in range(rows)
        for col in range(columns)
    ]


def build_onq_mount(p: Parameters = Parameters()) -> cq.Workplane:
    """Build the OnQ tripod (column_offset > 0) or tetrapod (otherwise)."""
    if p.plate_height <= 0 or p.plate_thickness <= 0:
        raise ValueError("Plate height and thickness must be positive")
    if p.pin_diameter <= 0 or p.pin_length <= 0:
        raise ValueError("Pin diameter and length must be positive")

    pin_radius = p.pin_diameter / 2.0
    pin_width = 4.0 * pin_radius / sqrt(5.0)
    pair_height = p.vertical_spacing + p.pin_diameter

    plate_offset = (
        max(0.0, (pair_height - p.plate_height) / 2.0)
        if p.column_offset > 0
        else 0.0
    )

    pin = make_pin(p, pin_radius, pin_width)
    parts: list[cq.Shape] = []

    # First pin pair, at the near end of the plate.
    parts.extend(pin_pair_parts(p, pin, pin_radius, pin_width))

    if p.column_offset > 0:
        # Tripod: one pin at the far end. The support is centered on that pin.
        far_pin_x = p.column_offset + pin_radius
        far_pin = (
            pin.rotate((0, 0, 0), (0, 0, 1), 180)
            .translate((far_pin_x, p.horizontal_spacing, p.slat_thickness - 0.1))
        )
        far_support = box_at(
            pair_height,
            pin_width,
            p.plate_thickness + p.slat_thickness,
            far_pin_x - pair_height / 2.0,
            p.horizontal_spacing - pin_width / 2.0,
            -p.plate_thickness,
        )
        parts.extend([far_pin, far_support])
        parts.extend(plate_parts(p, pin_width, plate_offset))
    else:
        # Tetrapod: a second pair, rotated 180 degrees at the far end.
        for item in pin_pair_parts(p, pin, pin_radius, pin_width):
            parts.append(
                item.rotate((0, 0, 0), (0, 0, 1), 180)
                .translate((pair_height, p.horizontal_spacing, 0))
            )
        parts.extend(plate_parts(p, pin_width))


    model = fuse_all(parts)

    return cq.Workplane("XY").newObject([model.clean()])


# Build the default tripod. Set column_offset = 0 for the tetrapod variant.
params = Parameters()
result = build_onq_mount(params)
edge = result.faces("<Z").edges(">X")
bb = edge.val().BoundingBox()

upper_thick = 7
upper_height = 60

height = -35.0 + params.plate_thickness - upper_thick
run = -params.plate_height

x = bb.xmax
z = bb.zmin
y0, y1 = bb.ymin, bb.ymax

first_thick = 8

# Create a triangular wedge along the selected edge.
wedge = (
    cq.Workplane("XZ", origin=(0, y1, 0))
    .polyline([
        (first_thick + 2, z),
        (x, z + height + 5),
        (x, z + height - first_thick),
        (x + run, z),
    ])
    .close()
    .extrude(y1 - y0)
)

# Merge wedge into original solid.
result = result.union(wedge).clean()

face = result.faces(">X").faces("<Y")
result = face

bb = face.val().BoundingBox()
upper = (
    cq.Workplane("YZ")
    .workplane(offset=bb.xmax)
    .center((bb.ymin + bb.ymax) / 2, bb.zmin + upper_thick / 2)
    .rect(bb.ylen, upper_thick)
    .extrude(upper_height)
)

result = result.union(upper)

result = result.faces(">X[1]").faces("<Z").edges("<Z").chamfer(5.5)

result = result.faces(">X").chamfer(1)

result = result.faces(">Y").edges("not >Z").chamfer(1)
result = result.faces("<Y").edges("not >Z").chamfer(1)

result = result.edges("<Z").edges("<X").chamfer(1)
result = result.faces("<X").edges("<Z").chamfer(1)


# In CQ-editor this displays the model. Uncomment the export line to save STEP/STL.
if "show_object" in globals():
    show_object(result, name="OnQ mounting plate")

cq.exporters.export(result, "onq_mount.step")
# cq.exporters.export(result, "onq_mount.stl")
