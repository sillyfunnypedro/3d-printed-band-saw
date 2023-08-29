from solid import *
from solid.utils import *
import os
import subprocess
import math


# Design tools that have nothing to do with the band saw.
class HelperTools:
    def __init__(self):
        self.bolt_sizes = dict()
        self.bolt_sizes["3mm"] = dict(bolt=3.3, nut=5, depth=3)
        self.bolt_sizes["4mm"] = dict(bolt=4.4, nut=6.7, depth=4)
        self.bolt_sizes["5mm"] = dict(bolt=5.5, nut=8, depth=5, flat=8.3)

        self.bolt_sizes["6mm"] = dict(bolt=6.4, nut=10, depth=5)
        self.bolt_sizes["7mm"] = dict(bolt=7.5, nut=12, depth=5)
        self.bolt_sizes["8mm"] = dict(bolt=8.0, nut=15.4, depth=6.5)
        self.bolt_sizes["8mm-rod"] = dict(bolt=8.5, nut=15.4, depth=6.5)
        self.bolt_sizes["5/16"] = dict(bolt=8.3, nut=15.2, depth=6.5)
        self.bolt_sizes["1/4"] = dict(bolt=6.9, nut=13.4, depth=5)

        self.round_bolt_sizes = dict()
        self.round_bolt_sizes["5mm"] = dict(bolt=5.5, nut=9.5, depth=5, flat=8.3)
        self.round_bolt_sizes["4mm"] = dict(bolt=4.5, nut=7.2, depth=5)

    def horizontal_cylinder_d(self, d, h, center=False, segments=30):
        obj = rotate((-90, 0, 0))(cylinder(d=d, h=h, center=center, segments=segments))
        return obj

    def horizontal_cylinder_d1d2(self, d1, d2, h, center=False, segments=30):
        obj = rotate((-90, 0, 0))(cylinder(d1=d1, d2=d2, h=h, center=center, segments=segments))
        return obj

    def horizontal_cylinder_r(self, r, h, center=False):
        obj = rotate((-90, 0, 0))(cylinder(r=r, h=h, center=center))
        return obj

    def round_bolt_hole_z(self, size, length, make_head=True):

        data = self.round_bolt_sizes[size]
        bolt_diameter = data['bolt']
        nut_diameter = data['nut']
        nut_depth = data['depth']
        if make_head:
            hole = cylinder(d=bolt_diameter, h=length + nut_depth, segments=30)
            # make the head part really long
            hole += translate((0, 0, -1000))(cylinder(d=nut_diameter, h=nut_depth + 1000, segments=30))
        else:
            hole = cylinder(d=bolt_diameter, h=1000, segments=30, center=True)
        return hole

    def round_bolt_hole_y(self, size, length, make_head=True):
        hole = rotate((-90, 0, 0))(self.round_bolt_hole_z(size, length, make_head))
        return hole

    def round_bolt_hole_x(self, size, length, make_head=True):
        hole = rotate((0, 90, 0))(self.round_bolt_hole_z(size, length, make_head))
        return hole

    def hexagonal_bolt_hole_z(self, size, length, make_head=True):

        data = self.bolt_sizes[size]
        bolt_diameter = data['bolt']
        nut_diameter = data['nut']
        nut_depth = data['depth']
        if make_head:
            hole = cylinder(d=bolt_diameter, h=length + nut_depth, segments=30)
            # make the hexagonal part really long
            hole += translate((0, 0, -1000))(cylinder(d=nut_diameter, h=nut_depth + 1000, segments=6))
        else:
            hole = cylinder(d=bolt_diameter, h=1000, segments=30, center=True)
        return hole

    def hexagonal_bolt_hole_y(self, size, length, make_head=True):
        hole = rotate((-90, 0, 0))(self.hexagonal_bolt_hole_z(size, length, make_head))
        return hole

    def hexagonal_bolt_hole_x(self, size, length, make_head=True):
        hole = rotate((0, 90, 0))(self.hexagonal_bolt_hole_z(size, length, make_head))
        return hole

    def three_bolts(self, size, length):  # test function to see if it all lines up
        three_bolts = translate((0, 0, 10))(self.hexagonal_bolt_hole_z(size, length))
        three_bolts += translate((0, 10, 0))(self.hexagonal_bolt_hole_y(size, length))
        three_bolts += translate((10, 0, 0))(self.hexagonal_bolt_hole_x(size, length))
        return three_bolts

    def wheel_cover(self, diameter, thickness, depth, cover_width):
        cover = translate((0, 0, thickness + 1))(cylinder(d=diameter + 2 * thickness, h=depth - 1))

        # cut out the insede
        cover -= cylinder(d=diameter, h=depth)

        cover -= cylinder(d=diameter - 2 * cover_width + 2 * thickness, h=300, center=True)

        cover -= cylinder(d=20, h=200, center=True)
        cover -= translate((-1000, 0, 0))(cube((2000, 2000, depth)))
        cover = rotate((-90, 0, 0))(cover)
        cover = scale((1, -1, 1))(cover)
        cover = translate((0, thickness + depth, 0))(cover)
        square_cutter = translate((-diameter / 2 + cover_width - thickness, -150, -diameter / 2 - 30))(
            cube((300, 300, diameter / 2 + 30)))
        cutter = translate((80, 0, -100))(
            rotate((90, 0, 0))(
                cylinder(d=diameter * 1.8, h=300, center=True)
            )
        )
        cover -= square_cutter

        def spoke(length, angle):
            spoke = translate((0, -5, 0))(cube((length, 10, thickness)))
            spoke = rotate((0, 0, angle))(spoke)

            return spoke

        # make the cover for the left hand side of the blade only.
        cover = cover - translate((-50, -1000, -1000))(cube((2000, 2000, 2000)))

        return cover


class BandSaw:
    def __init__(self):
        self.make_stl = False  # this is turned off for debuging
        self.production = False # this is turned on for production

        # initialize the tools.
        self.tools = HelperTools()

        # the width of the main c_frame.  It makes sense for this to be very thick. since it supports
        # the tension between the top and bottom wheels, and also has some side twist to help align
        # the blade
        self.c_form_width = 43

        # the width of the front and back plates
        self.front_plate_thickness = 14
        self.back_plate_thickness = 23  # give an extra  2 millimiters for the collet and axle to flow through
        self.bottom_axle_access_diameter = 25

        # the radii
        self.big_radius = 185
        self.small_radius = 125

        # the extension of the brace that holds the c_form, also the base for the blade protector
        # at the back
        self.c_form_brace_extension = 65

        # The width of the plates
        self.plate_width = 14

        # distance of wheel from frame
        self.wheel_offset_from_frame = 6.5

        # THE BASE
        # The thickness of the base.  This is also quite important to be thick since it does provide some weight
        # and stability to the band saw
        self.base_thickness = 25
        self.base_is_square = False  # Set to true if you want a squre base.

        # The width and length of the base 200 is the original, might make sense to make it wider for extra stability.
        # To be figured out on the first prototype.
        self.base_width = 200
        self.base_length = 350
        self.base_corner_radius = 30

        # the variables for the top bearing holder and slider and stuff
        self.top_bearing_tab_depth = 5
        self.top_bearing_tab_thickness = 10
        self.top_bearing_holder_height = 80
        self.top_bearing_holder_width = 40
        self.top_bearing_bottom_of_slot = 30
        self.top_bearing_extension_height = 165
        self.top_bearing_slide_capability = 8  # how much room above the holder
        self.top_bearing_body_depth = self.c_form_width - self.top_bearing_tab_thickness
        self.top_bearing_body_gap = 0.75

        # THE SUB_BASE
        # This is the part that connects to the base and suppors the sides that are bolted together to hold the c_frame
        # in place.
        self.sub_base_total_height = 178
        self.sub_base_top_section_length = 178
        self.sub_base_bottom_section_thick_length = 199
        self.sub_base_bottom_section_thin_length = 340
        self.sub_base_bottom_section_thick_height = 52
        self.sub_base_bottom_section_thin_height = 25

        # the base connects to the sub_base.
        self.number_of_base_bolts = 5

        # the wheels that need to be printed.
        self.wheel_diameter = 142
        self.wheel_thickness = 27
        self.bearing_8mm_od = 22.5

        # the data for the table top
        self.table_top_width = 240

        self.table_top_depth = 200  # the amount that comes forward from the front of the back plate
        self.table_top_thickness = 20
        self.table_top_offset_from_holder = 87
        self.table_top_corner_radius = 10

        self.table_top_cutout_diameter = 50
        self.table_top_cutout_extra = 5
        self.table_top_cutout_depth = 5
        self.make_center_hole_square = True

        # miter variables

        self.table_top_miter_thickness = 10
        self.table_top_miter_radius = 60
        self.table_top_miter_hole_offset = self.table_top_miter_radius * .4
        self.table_top_miter_set_angles = [0, 30, 45]
        self.table_top_miter_back_plate_thickness = 5
        self.table_top_miter_back_plate_depth = 15
        self.table_top_miter_peg_offset_factor = .7

        # fence variables

        self.fence_height = 60
        self.fence_width = 20
        self.fence_attachment_width = 100
        self.fence_guide_depth = 5  # this determines the size and dept of the the slot on the front
        # and back of the table for the fence guide
        self.table_fence_nut_depth = 25

        # The guide for the blade
        self.guide_plate_top_height = 193
        self.guide_plate_bottom_height = 120
        self.guide_plate_thickness = 22
        self.guide_tongue_thickness = 16
        self.guide_tongue_width = 10
        self.guide_small_groove = self.tools.bolt_sizes["1/4"]["bolt"] + .2  # to give it more slide
        self.guide_large_groove = 14
        self.guide_large_groove_depth = 5
        self.guide_groove_from_top = 20
        self.guide_groove_from_bottom = 50
        self.guide_plate_bolt_diameter = 4.4
        self.guide_plate_nut_diameter = 9

        # back plate values
        self.back_plate_height = 178
        # Where is the tip of the back plate (we need his for the attachment calculatioins
        self.back_plate_length = 340
        self.back_plate_tip = (
            self.back_plate_length, self.back_plate_thickness + self.c_form_width / 2, self.back_plate_height)

        # Table values

        self.table_vertical_plate_height = 120
        self.table_vertical_plate_width = 121
        self.table_vertical_plate_thickness = 30
        self.table_slide_holder_width = 20

        self.table_attachment_top_thickness = 10
        self.table_distance_from_tip = 16
        self.table_connector_bolt_separation = 30

        self.table_guide_slot_width = 20
        self.table_miter_slot_depth = 10
        self.table_guide_champher = 0
        self.table_top_guide_offset = 40
        self.table_top_guide_bar_length = self.table_top_depth + 50

        # blade protectore values
        self.blade_protector_thickness = 5
        self.blade_protector_extension_ammount = 10  # The extra space in the protector
        self.blade_protector_depth = self.wheel_thickness + self.blade_protector_extension_ammount
        self.blade_protector_height = 200
        self.blade_protector_cover_thickness = 5
        self.blade_protector_riser_front_width = 20
        self.blade_protector_cover_diameter_extendor = 8
        self.blade_cover_radius = self.small_radius - 10

        # here we calculate the center of the c-form and store it
        bottom_height = 52 + 13  # from the diagaram, to calculate the center of the c_frame

        self.center_x = self.big_radius
        self.center_y = -self.c_form_width / 2
        self.center_z = bottom_height + self.big_radius

        # the list of all the parts to print
        self.parts = [[self.base_bottom_part, True],
                      [self.base_center_plate, True],
                      [self.full_assembly, False],
                      [self.c_form, True],
                      [self.base_front_plate, True],
                      [self.base_back_plate, True],
                      [self.bottom_wheel, True],
                      [self.top_wheel, True],
                      [self.top_blade_guide, True],
                      [self.bottom_blade_guide, True],
                      [self.upper_blade_guide_bearing_holder, True],
                      [self.lower_blade_guide_bearing_holder, True],
                      [self.blade_guide_bearing_holder_v2, False],
                      [self.table_slider_attachment, True],
                      [self.table_top, True],
                      [self.fence_bar, True],
                      [self.fence_bar_attachment_front, True],
                      [self.fence_bar_attachment_back, True],
                      [self.table_slider_holder_panel, True],
                      [self.blade_protector_cover, True],
                      [self.blade_protector_cover_top, False],
                      [self.blade_protector_cover_bottom, False],
                      [self.blade_protector_cover_connector, False],
                      [self.lower_bearing_test, False],
                      [self.top_wheel_axle_bearing_holder, True],
                      [self.table_top_miter_bar, True],
                      [self.table_top_miter, True],
                      [self.top_bearing_back_plate, True],
                      [self.test_wheel_connection, False],
                      [self.test_wheels, False],
                      [self.test_bolts_bar, False],
                      [self.test_c_form_groove, False],
                      [self.hexagonal_grinder_holder, False],
                      [self.square_grinder_holder, False],
                      [self.throttle_controller, True],
                      [self.c_form_250, False],
                      ]

        self.parts2 = [[self.base_bottom_part, True],
                      [self.base_center_plate, True],
                      [self.c_form, True],
                      [self.base_front_plate, True],
                      [self.base_back_plate, True],
                      [self.bottom_wheel, True],
                      [self.top_wheel, True],
                      [self.top_blade_guide, True],
                      [self.bottom_blade_guide, True],
                      [self.upper_blade_guide_bearing_holder, True],
                      [self.lower_blade_guide_bearing_holder, True],
                      [self.table_slider_attachment, True],
                      [self.table_top, True],
                      [self.fence_bar, True],
                      [self.fence_bar_attachment_front, True],
                      [self.fence_bar_attachment_back, True],
                      [self.table_slider_holder_panel, True],
                      [self.blade_protector_cover, True],
                      [self.top_wheel_axle_bearing_holder, True],
                      [self.table_top_miter_bar, True],
                      [self.table_top_miter, True],
                      [self.top_bearing_back_plate, True],
                      [self.throttle_controller, True],
                      [self.base_bottom_part, False],
                      [self.base_center_plate, False],
                      [self.full_assembly, False],
                      [self.c_form, False],
                      [self.blade_guide_bearing_holder_v2, False],
                      [self.blade_protector_cover_top, False],
                      [self.blade_protector_cover_bottom, False],
                      [self.blade_protector_cover_connector, False],
                      [self.lower_bearing_test, False],
                      [self.test_wheel_connection, False],
                      [self.test_wheels, False],
                      [self.test_bolts_bar, False],
                      [self.test_c_form_groove, False],
                      [self.hexagonal_grinder_holder, False],
                      [self.square_grinder_holder, False],
                      [self.c_form_250, False],
                      ]

        # prepare for where we dump the scad files.
        home = os.path.expanduser("~")
        # get the path for the current working directory
        current_directory = os.path.dirname(os.path.realpath(__file__))
        self.output_directory = os.path.join(current_directory, "outputs")

        # if you want your production files to go somewhere else, Uncomment following line
        #self.production_output_directory = os.path.join(self.output_directory, "production")

        self.production_output_directory = self.output_directory

        # make the output directory if it doesn't exist
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
        if not os.path.exists(self.production_output_directory):
            os.makedirs(self.production_output_directory)

    def full_assembly(self):
        name = "full_assembly"
        rotation = 0
        table_height = 0
        base = self.base_bottom_part()[0]
        sub_base = self.base_center_plate()[0]
        c_form = self.c_form()[0]
        front_plate = self.base_front_plate()[0]
        back_plate = self.base_back_plate()[0]
        bottom_wheel = self.bottom_wheel()[0]
        top_wheel = self.top_wheel()[0]
        top_blade_guide = self.top_blade_guide()[0]
        bottom_blade_guide = self.bottom_blade_guide()[0]
        upper_blade_guide_bearing_holder = self.upper_blade_guide_bearing_holder()[0]
        lower_blade_guide_bearing_holder = self.lower_blade_guide_bearing_holder()[0]
        table_attachment = self.table_slider_attachment()[0]
        table_top = self.table_top()[0]
        table_slider_holder_panel = self.table_slider_holder_panel()[0]
        blade_protector_cover = self.blade_protector_cover()[0]
        blade_protector_cover_connector = self.blade_protector_cover_connector()[0]
        top_bearing_holder = self.top_wheel_axle_bearing_holder()[0]
        top_bearing_back_plate = self.top_bearing_back_plate()[0]
        table_top_guide_bar = self.table_top_miter_bar()[0]
        fence_bar = self.fence_bar()[0]
        fence_attachment_front = self.fence_bar_attachment_front()[0]
        fence_attachment_back = self.fence_bar_attachment_back()[0]
        table_top_miter = self.table_top_miter()[0]
        table_top_guide_bar += table_top_miter

        band_saw = base
        band_saw += sub_base
        rotatable_body = c_form

        rotatable_body += bottom_wheel
        rotatable_body += top_wheel
        rotatable_body += top_blade_guide
        rotatable_body += bottom_blade_guide
        rotatable_body += upper_blade_guide_bearing_holder
        rotatable_body += lower_blade_guide_bearing_holder
        rotatable_body += self.blade()
        rotatable_body += blade_protector_cover
        rotatable_body += top_bearing_holder
        rotatable_body += top_bearing_back_plate

        rotatable_body = translate((-self.center_x, 0, -self.center_z))(rotatable_body)
        rotatable_body = rotate((0, -rotation, 0))(rotatable_body)
        rotatable_body = translate((self.center_x, 0, self.center_z))(rotatable_body)

        band_saw += rotatable_body
        # band_saw+=c_form

        band_saw += front_plate
        band_saw += back_plate

        table = table_attachment
        table += table_top
        table += table_top_guide_bar
        table += fence_bar
        # table += fence_attachment_front
        # table += fence_attachment_back
        table += table_slider_holder_panel

        band_saw += translate((0, 0, table_height))(table)

        # band_saw += blade_protector_cover_connector

        return band_saw, name

    def full_assembly_animated(self):
        name = "full_assembly_animated"
        rotation = 0
        table_height = 0
        base = self.base_bottom_part()[0]
        sub_base = self.base_center_plate()[0]
        c_form = self.c_form()[0]
        front_plate = self.base_front_plate()[0]
        back_plate = self.base_back_plate()[0]
        bottom_wheel = self.bottom_wheel(top=False)[0]
        top_wheel = self.top_wheel(top=True)[0]
        top_blade_guide = self.top_blade_guide()[0]
        bottom_blade_guide = self.bottom_blade_guide()[0]
        upper_blade_guide_bearing_holder = self.upper_blade_guide_bearing_holder()[0]
        lower_blade_guide_bearing_holder = self.lower_blade_guide_bearing_holder()[0]
        table_attachment = self.table_slider_attachment()[0]
        table_top = self.table_top()[0]
        table_slider_holder_panel = self.table_slider_holder_panel()[0]
        blade_protector_cover = self.blade_protector_cover()[0]
        blade_protector_cover_connector = self.blade_protector_cover_connector()[0]
        top_bearing_holder = self.top_wheel_axle_bearing_holder()[0]
        top_bearing_back_plate = self.top_bearing_back_plate()[0]
        table_top_guide_bar = self.table_top_miter_bar()[0]
        fence_bar = self.fence_bar()[0]
        fence_attachment_front = self.fence_bar_attachment_front()[0]
        fence_attachment_back = self.fence_bar_attachment_back()[0]
        table_top_miter = self.table_top_miter()[0]
        table_top_guide_bar += table_top_miter
        # take all the objects defined above and put them in a list
        objects = [
            base,
            sub_base,
            c_form,
            front_plate,
            back_plate,
            bottom_wheel,
            top_wheel,
            top_blade_guide,
            bottom_blade_guide,
            upper_blade_guide_bearing_holder,
            lower_blade_guide_bearing_holder,
            table_attachment,
            table_top,
            table_slider_holder_panel,
            blade_protector_cover,
            blade_protector_cover_connector,
            top_bearing_holder,
            top_bearing_back_plate,
            table_top_guide_bar,
            fence_bar,
            fence_attachment_front,
            fence_attachment_back,
            table_top_miter

        ]
        # start a timer to keep track of the animation.  the timer will iterate over the number of objects in the list
        for i in range(len(objects)):

            band_saw = base
            if i > 0:
                band_saw += sub_base
            if i > 1:
                band_saw += front_plate
            if i > 2:
                band_saw += back_plate
            rotatable_body = c_form
            if i > 3:
                rotatable_body += bottom_wheel
            if i > 4:
                rotatable_body += top_wheel
                rotatable_body += self.blade()
            if i > 5:
                rotatable_body += top_blade_guide
            if i > 6:
                rotatable_body += bottom_blade_guide
            if i > 7:
                rotatable_body += upper_blade_guide_bearing_holder
            if i > 8:
                rotatable_body += lower_blade_guide_bearing_holder
            if i > 9:
                rotatable_body += blade_protector_cover
            if i > 10:
                rotatable_body += top_bearing_holder
                rotatable_body += top_bearing_back_plate

            rotatable_body = translate((-self.center_x, 0, -self.center_z))(rotatable_body)
            rotatable_body = rotate((0, -rotation, 0))(rotatable_body)
            rotatable_body = translate((self.center_x, 0, self.center_z))(rotatable_body)
            if i > 3:
                band_saw += rotatable_body
            # band_saw+=c_form

            table = table_attachment
            if i > 11:
                table += table_top
            if i > 12:
                table += table_top_guide_bar
            if i > 13:
                table += fence_bar
            if i > 14:
                table += fence_attachment_front
                table += fence_attachment_back
            if i > 15:
                table += table_slider_holder_panel
            if i > 11:
                band_saw += translate((0, 0, table_height))(table)
            self.render(band_saw, name, "full_assembly_animated")
            # print a prompt and then wait for user to hit return
            input("press enter to continue")
        # band_saw += blade_protector_cover_connector

        return band_saw, name

    ####################################################################################################################
    #                                                                                                                  #
    # render all the parts in the self.parts list                                                                      #
    #                                                                                                                  #
    # Some parts are rendered individually, others are rendered as a group.  The group is defined by the __SEGMENTS__  #
    # name.  If the object name is __SEGMENTS__ then the object is a list of dictionaries.  Each dictionary contains   #
    # the object to be rendered, the name of the object, and the stl file name.  The object is rendered individually   #
    #                                                                                                                  #
    ####################################################################################################################
    def render_all(self):
        for part in self.parts:

            func = part[0]
            stl = part[1]
            result = func()
            obj = result[0]
            name = result[1]
            if len(result) == 3:
                obj = result[2]

            # if we are in production mode and the stl value for this part is False then skip it
            if self.production and not stl:
                print("Skipping {}, because not a production file".format(name))
                continue

            # If the object name is not __SEGMENTS__ then render it individually
            if name != "__SEGMENTS__":
                self.render(obj, name, stl)
            else:
                # If the object name is __SEGMENTS__ then render each segment individually
                for segment in obj:
                    sub_obj = segment["obj"]
                    sub_name = segment["name"]
                    sub_stl = segment["stl"]
                    self.render(sub_obj, sub_name, sub_stl)

    ##################################################################
    # Make the file path templates for the scad and stl files
    ##################################################################
    def make_file_path_templates(self, name):
        output_scad_file = os.path.join(self.output_directory, "{}.scad".format(name))
        output_stl_file = os.path.join(self.output_directory, "{}.stl".format(name))
        if self.production:
            output_scad_file = os.path.join(self.production_output_directory, "{}.scad".format(name))
            output_stl_file = os.path.join(self.production_output_directory, "{}.stl".format(name))
        return output_scad_file, output_stl_file

    ##################################################################
    # Render the object to scad and stl files

    ##################################################################
    def render(self, obj, name, stl):
        output_scad_file, output_stl_file = self.make_file_path_templates(name)
        print("Rendering {} to {}".format(name, output_scad_file))
        scad_render_to_file(obj, output_scad_file, include_orig_code=False)
        if self.make_stl and stl:
            # assuming that we cleared out the files before the run
            # check to see if the stl file exists
            if not os.path.isfile(output_stl_file):
                self.make_stl_file_command(output_scad_file, output_stl_file)

    ##################################################################
    # Run the stl converter.
    #
    # WARNING:   this can take a long time
    ##################################################################

    def make_stl_file_command(self, scad_file, stl_file):
        command_list = ['/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD', '-o', stl_file, scad_file]
        print("Creating the stl file {}".format(stl_file))
        subprocess.call(command_list)

    ##################################################################
    # Th base of the band saw

    def base_bottom_part(self):
        name = "base_bottom_part"

        base = hull()(
            translate((self.base_corner_radius, self.base_width / 2 - self.base_corner_radius, 0))(
                cylinder(r=30, h=self.base_thickness)),
            translate((self.base_corner_radius, -self.base_width / 2 + self.base_corner_radius, 0))(
                cylinder(r=30, h=self.base_thickness)),
            translate((self.base_length - self.base_corner_radius, self.base_width / 2 - self.base_corner_radius, 0))(
                cube((self.base_corner_radius, self.base_corner_radius, self.base_thickness))),
            translate((self.base_length - self.base_corner_radius, -self.base_width / 2, 0))(
                cube((self.base_corner_radius, self.base_corner_radius, self.base_thickness))),

        )
        # this is all based on hacking together the original base from the wood design.
        # If the width and length are changed then this needs to be fixed.
        # here we are cutting out the sides with that elegant curve in the original design.
        # If you just want a square set self.base_is_square = True
        segments = 30

        if not self.base_is_square:
            big_circle_diameter = 790
            offset = big_circle_diameter / 2 + 70
            base = difference()(base, translate((self.base_length / 2, offset, -10))(
                cylinder(d=big_circle_diameter, h=self.base_thickness * 2, segments=segments)))
            base = difference()(base, translate((self.base_length / 2, -offset, -10))(
                cylinder(d=big_circle_diameter, h=self.base_thickness * 2, segments=segments)))

        # move the base down by the thickness so the rest starts from the x_y plane
        base = translate((0, 0, -self.base_thickness))(base)
        # Now cut out the bolt holes so we can connect to sub_base

        base = base - self.base_connector_bolt_holes()

        return base, name

    ##################################################################
    # The front plate of the three plates that attach to the base and
    # support the c_form between them
    ##################################################################
    def base_front_plate(self):
        name = "base_front_plate"
        plate = hull()(
            cube([100, self.front_plate_thickness, 210]),
            translate((33, 0, 220))(self.tools.horizontal_cylinder_d(d=50, h=self.front_plate_thickness))
        )
        plate -= self.big_circle_parametric(self.small_radius + 5, thickness=self.c_form_width)
        plate = translate((0, -self.front_plate_thickness - self.c_form_width / 2, 0))(plate)

        plate += self.inner_slider()

        plate = intersection()(
            plate,
            translate((0, -100.5, 0))(
                cube([200, 100, 500])
            )
        )

        plate = plate - self.side_sub_base_connector_bolt_holes()
        # plate = self.side_sub_base_connector_bolt_holes()
        printable = rotate((90, 0, 0))(plate)
        return plate, name, printable

    ##################################################################
    # The SUB_BASE is two parts in the wooden version of this band saw.
    # It made sense to print them together to avaid having to join them.
    # This is the middle of the three platest that attach to the base and
    # support the c_form between them
    # this base has been extened out to the front to provide support to
    # the back plate of the support.  This was done to make the support of
    # the table of the saw more secure.
    ##################################################################
    def base_center_plate(self):
        name = "base_center_plate"

        sub_base_top_section_height = self.sub_base_total_height - self.sub_base_bottom_section_thick_height

        # in the original design these are two pieces of wood that are screwed together
        # here we will print them together
        # First lets build the nice bottom of the sub_base.
        bottom = translate((0, -self.c_form_width / 2, 0))(
            hull()(
                cube((10, self.c_form_width, self.sub_base_bottom_section_thick_height)),
                translate((self.sub_base_bottom_section_thick_length - 20, 0, 0))(cube((20, self.c_form_width, 20))),
                translate((self.sub_base_bottom_section_thick_length - 20, 0,
                           self.sub_base_bottom_section_thick_height - 20))(
                    self.tools.horizontal_cylinder_r(r=20, h=self.c_form_width))
            )
        )

        # now lets extend it
        bottom += translate((0, -self.c_form_width / 2, 0))(
            hull()(
                cube((10, self.c_form_width, self.sub_base_bottom_section_thin_height)),
                translate((self.sub_base_bottom_section_thin_length - 12, 0, 0))(cube((12, self.c_form_width, 12))),
                translate(
                    (self.sub_base_bottom_section_thin_length - 12, 0, self.sub_base_bottom_section_thin_height - 12))(
                    self.tools.horizontal_cylinder_r(r=12, h=self.c_form_width))
            )
        )

        # now lets build the curved part of the subbase that will have the c_frame resting on it.
        # shove the top down by .1 to make sure they are stuck together in one piece.
        epsilon_glue = 0.1
        top = translate((0, -self.c_form_width / 2, self.sub_base_bottom_section_thick_height - epsilon_glue))(
            hull()(
                cube([10, self.c_form_width, 10]),
                translate((5, 0, sub_base_top_section_height - 5 + epsilon_glue))(
                    self.tools.horizontal_cylinder_r(r=5, h=self.c_form_width)),
                translate((self.sub_base_top_section_length - 10, 0, 0))(
                    cube([10, self.c_form_width, 10])),
                translate((self.sub_base_top_section_length - 5, 0, sub_base_top_section_height - 5 + epsilon_glue))(
                    self.tools.horizontal_cylinder_r(r=5, h=self.c_form_width))
            )
        )
        top = top - self.big_circle_parametric(self.big_radius + 0.5, thickness=self.c_form_width)

        sub_base = bottom + top

        bolt_holes = self.base_connector_bolt_holes()
        sub_base = sub_base - bolt_holes

        sub_base = sub_base - self.side_sub_base_connector_bolt_holes()

        return sub_base, name

    ##################################################################
    # The back plate of the three plates that attach to the base and
    # support the c_form between them
    ##################################################################
    def base_back_plate(self):
        name = "base_back_plate"

        plate = self.base_back_plate_solid(self.back_plate_thickness)

        plate = translate((0, self.c_form_width / 2, 0))(plate)
        plate += self.inner_slider()

        plate -= translate((0, 42, 0))(self.axle_cutout_for_back_plate())
        plate = intersection()(
            plate,
            cube([1000, 100, 500])
        )
        plate = plate - self.bottom_axle(self.bottom_axle_access_diameter)

        plate = plate - self.side_sub_base_connector_bolt_holes()

        plate = plate - self.table_connector_bolt_holes()

        plate = plate - translate((0, self.c_form_width / 2, 0))(self.table_holder_slide_bolt_holes())
        printable = rotate((-90, 0, 0))(plate)

        return plate, name, printable

    ##################################################################
    # the solid part that is constructed to make the back_plate.
    # This is a seperate function so that it can be used to make the
    # back plate for the saw.  the holes are cut out in base_back_plate
    ##################################################################
    def base_back_plate_solid(self, thickness):

        # the part at the far left of the plate that rises up to hold the slider for the c_frame
        plate = hull()(
            cube([100, thickness, 210]),
            translate((33, 0, 220))(self.tools.horizontal_cylinder_d(d=50, h=thickness))
        )
        # Cut out the big cicrle to make it look nice.
        plate -= self.big_circle_parametric(self.small_radius + 5, thickness=2000)

        bottom_length = self.sub_base_bottom_section_thin_length
        arm = cube((bottom_length, thickness, self.back_plate_height))

        # the bottom part of the plate.
        plate += arm
        height = 178

        top_length = 178

        radius = 20
        bottom_height = 52
        top_height = height - bottom_height
        bottom = hull()(
            cube([10, thickness, bottom_height]),

            translate((bottom_length - radius, 0, 0))(cube((radius, thickness, 20))),
            translate((bottom_length - radius, 0, bottom_height - radius))(
                rotate((-90, 0, 0))(cylinder(r=radius, h=thickness)))
        )

        plate += bottom

        # shove the top down by .1 to make sure they are stuck together in one piece.
        epsilon_glue = 0.1
        plate += translate((0, 0, bottom_height - epsilon_glue))(
            hull()(
                cube([10, thickness, 10]),
                translate((5, 0, top_height - 5 + epsilon_glue))(rotate((-90, 0, 0))(cylinder(r=5, h=thickness))),
                translate((top_length - 10, 0, 0))(cube([10, thickness, 10])),
                translate((top_length - 5, 0, top_height - 5 + epsilon_glue))(
                    rotate((-90, 0, 0))(cylinder(r=5, h=thickness)))
            )
        )

        return plate

    ##################################################################
    # a utility function to carve out the groove in the center piece
    # it is parametrized by the top angle of the groove and the bottom angle
    # of the groove.  The large diameter and small diameter of the groove
    # are also parameters.
    ################################################################## acti
    def c_form_groove(self, bottom_angle=30, top_angle=-30, large_diameter=168, small_diameter=142):
        # make a solid of the groove that is to be cut out.
        segments = 20
        if self.production:
            segments = 100
        center_of_groove = (large_diameter + small_diameter) / 2.0
        groove = self.big_circle_parametric(large_diameter, self.c_form_width) - \
                 self.big_circle_parametric(small_diameter, self.c_form_width)

        # cut the bottom out
        cutter = rotate((0, bottom_angle, 0))(
            translate((0, 0, -300))(
                cube((400, 100, 600))
            ))
        groove = groove - translate((self.center_x, self.center_y, self.center_z))(
            cutter
        )

        # cut the top off
        cutter = rotate((0, top_angle, 0))(
            translate((0, 0, -300))(
                cube((400, 100, 600))
            ))
        groove = groove - translate((self.center_x, self.center_y, self.center_z))(
            cutter
        )

        groove_end_diameter = large_diameter - small_diameter
        groove += translate((self.center_x, 0, self.center_z))(
            rotate((0, bottom_angle, 0))(
                translate((0, 0, -center_of_groove))(
                    rotate((90, 0, 0))(
                        cylinder(d2=groove_end_diameter, d1=groove_end_diameter, h=self.c_form_width, center=True,
                                 segments=segments)
                    )

                )
            )
        )
        groove += translate((self.center_x, 0, self.center_z))(
            rotate((0, top_angle, 0))(
                translate((0, 0, center_of_groove))(
                    rotate((90, 0, 0))(
                        cylinder(d2=groove_end_diameter, d1=groove_end_diameter, h=self.c_form_width, center=True,
                                 segments=segments)
                    )

                )
            )
        )

        groove = translate((0, 0, 0))(groove)
        return groove

    # this is here for cutting out the material as per the wood version
    def top_cut(self):
        obj = translate((self.center_x - 35, self.center_y, self.center_z))(
            cube((70, 12, 400))
        )

        obj += translate((self.center_x - 25, self.center_y, self.center_z))(
            cube((50, 16, 400))
        )
        obj += translate((self.center_x - 25, self.center_y, self.center_z + 185 - 4))(
            cube((50, 60, 8))
        )
        return obj

    def guide_and_axle_cutout(self):
        # the slot for the blade guide at the top
        obj = translate((self.center_x + 60, 0, self.center_z))(self.blade_guide_shape(2000))

        # the slot for the blade guide at the bottom
        obj += translate((self.center_x + 60, 0, self.center_z - self.small_radius - self.guide_plate_top_height))(
            self.blade_guide_shape(200))

        obj += translate((self.center_x, self.center_y, self.center_z + 125 + 20))(
            hull()(
                rotate((90, 0, 0))(
                    cylinder(d=10, h=100, center=True)
                ),
                translate((0, 0, 20))(
                    rotate((90, 0, 0))(
                        cylinder(d=10, h=100, center=True)
                    )
                )
            )

        )

        return obj

    def blade_protector_cover_connector_bolt_holes(self):
        origin_x = self.get_blade_protector_origin()[0]
        bolt_origin_y = -self.blade_protector_depth - self.c_form_width / 2 + self.blade_protector_cover_thickness

        bolt_offsets = [
            [-10, 60],
            [-10, 40],
            [-10, 20],
            [-38, 60],
            [-48, 40],
            [-55, 20]

        ]
        bolt_offsets_z = [-70, -40, -15, 15, 40, 70]
        holes = None
        for p in bolt_offsets:
            hole = translate((origin_x + p[0], bolt_origin_y, self.center_z + p[1]))(
                scale((1, -1, 1))(self.tools.hexagonal_bolt_hole_y(size="4mm", length=40))
            )
            hole += translate((origin_x + p[0], bolt_origin_y, self.center_z - p[1]))(
                scale((1, -1, 1))(self.tools.hexagonal_bolt_hole_y(size="4mm", length=40))
            )
            if holes:
                holes += hole
            else:
                holes = hole
        return holes

    def juancho_logo(self):
        logo = linear_extrude(height=30)(text("SFP 2023", font="Courier New:style=Bold", size=8, halign="center"))
        logo = rotate((90, 0, 0))(logo)
        return logo

    def blade_protector_cover_connector(self):
        name = "blade_protector_cover_connector"
        connector, _ = self.blade_protector_cover()
        slice = 158
        connector = intersection()(
            connector,
            translate((0, -400, self.center_z - slice / 2))(cube((800, 800, slice)))
        )
        connector -= translate((0, -self.blade_protector_depth - self.c_form_width / 2, 0))(cube((500, 1300, 500)))

        connector -= self.blade_protector_cover_connector_bolt_holes()
        connector = translate((0, -self.blade_protector_cover_thickness, 0))(connector)

        origin = self.get_blade_protector_origin()
        logo = self.juancho_logo()
        logo = translate((origin[0] - 33, origin[1] - self.blade_protector_cover_thickness * 2 + 2, origin[2] - 4))(
            logo)
        connector -= logo

        return connector, name

    # the front plate of rhte cover.
    def blade_protector_cover(self, connector_holes=False):
        name = "blade_protector_cover"
        origin_x, origin_y, origin_z = self.get_blade_protector_origin()

        outer_cover = self.big_circle_parametric(self.blade_cover_radius + 2 * self.blade_protector_cover_thickness + 2,
                                                 self.blade_protector_depth - 1)
        outer_cover -= self.big_circle_parametric(self.blade_cover_radius + 2,
                                                  self.blade_protector_depth - 2)
        cutter = (translate((origin_x - self.blade_protector_riser_front_width, -200, 0))(cube((2000, 4000, 500))))
        outer_cover -= cutter

        cover = outer_cover

        cover += self.big_circle_parametric(self.blade_cover_radius + 2,
                                            self.blade_protector_cover_thickness)
        cover = translate((0, -self.blade_protector_depth - self.blade_protector_cover_thickness, 0))(cover)
        cut_x = origin_x
        cutter = (translate((cut_x, -200, 0))(cube((2000, 400, 500))))
        cover -= cutter

        # riser
        riser_height = (self.big_radius + self.small_radius) / 2
        riser = cube(
            (self.blade_protector_riser_front_width, self.blade_protector_cover_thickness, riser_height * 2))
        riser += cube((self.blade_protector_cover_thickness, self.blade_protector_depth - 1, riser_height * 2))

        riser = translate((0, 0, -riser_height))(riser)

        ################
        # WHEEL COVER
        ################
        wheel_cover = self.tools.wheel_cover(self.wheel_diameter + self.blade_protector_cover_diameter_extendor,
                                             self.blade_protector_cover_thickness,
                                             self.blade_protector_depth,
                                             self.blade_protector_riser_front_width)
        x_offset = self.center_x - cut_x
        top_wheel_cover = translate((self.blade_protector_riser_front_width + x_offset, 0, riser_height))(wheel_cover)
        riser += top_wheel_cover

        bottom_wheel_cover = translate((self.blade_protector_riser_front_width + x_offset, 0, -riser_height))(
            scale((1, 1, -1))(wheel_cover)
        )

        riser += bottom_wheel_cover

        riser = translate((origin_x - self.blade_protector_riser_front_width,
                           -self.c_form_width / 2 - self.blade_protector_depth - self.blade_protector_cover_thickness,
                           origin_z))(riser)
        cover += riser
        circle_cutter = self.big_circle_parametric(self.blade_cover_radius + 5, self.blade_protector_depth)
        circle_cutter = translate((0, -self.blade_protector_depth, 0))(circle_cutter)

        cover -= circle_cutter

        cover -= self.blade_protector_bolts()

        bottom_cutter = cube((200, 50, 100))
        bottom_cutter = translate((origin_x - self.blade_protector_riser_front_width + 40,
                                   -self.c_form_width / 2 - self.blade_protector_depth, 0))(bottom_cutter)
        cover -= bottom_cutter

        if connector_holes:
            cover -= translate((0, -self.blade_protector_cover_thickness, 0))(
                self.blade_protector_cover_connector_bolt_holes())
        else:
            origin = self.get_blade_protector_origin()
            logo = self.juancho_logo()
            logo = translate((origin[0] - 33, origin[1] - self.blade_protector_cover_thickness + 2, origin[2] - 4))(
                logo)
            cover -= logo
        return cover, name

    def blade_protector_cover_top(self):
        name = "blade_protector_cover_top"
        cover, _ = self.blade_protector_cover(True)

        cutter = translate((-500, -500, self.center_z - 500))(cube((1000, 1000, 500)))
        cover -= cutter
        return cover, name

    def blade_protector_cover_bottom(self):
        name = "blade_protector_cover_bottom"
        cover, _ = self.blade_protector_cover(True)

        cutter = translate((-500, -500, self.center_z))(cube((1000, 1000, 500)))
        cover -= cutter
        return cover, name

    # the part of the blade protector at the back that is attached to the c_form
    def blade_protector_extension(self):

        # Frame of reference for the protector.  I am choosing the right side of the protector
        origin_x, origin_y, origin_z = self.get_blade_protector_origin()

        # The wall on the right hand of the protector.
        right_side = cube((self.blade_protector_thickness, self.blade_protector_depth, self.blade_protector_height))
        right_side = translate(
            (origin_x - self.blade_protector_thickness, origin_y, origin_z - self.blade_protector_height / 2))(
            right_side
        )

        # Now we build the left hand side of the extension for the protector.

        # the big circle is centered so adjust the y origin to compensate for that
        # the fo added to the raidus makes it a tighter fit with the cover
        left_side = translate((0, origin_y + self.c_form_width / 2, 0))(
            self.big_circle_parametric(self.blade_cover_radius + 4,
                                       self.blade_protector_depth))
        cut_x = origin_x - 20
        cutter = translate((cut_x, -200, 0))(cube((2000, 400, 500)))
        left_side -= cutter

        protector = right_side + left_side

        return protector

    def blade_protector_bolts(self):
        z_offset = 30
        y_offset = -self.c_form_width / 2
        x_offset = self.center_x - self.small_radius + 30

        bolt = scale((1, -1, 1))(self.tools.hexagonal_bolt_hole_y(size="1/4", length=120))
        bolts = translate((x_offset, y_offset, self.center_z + z_offset))(bolt)
        bolts += translate((x_offset, y_offset, self.center_z - z_offset))(bolt)
        return bolts

    def top_bearing_back_plate_bolts(self):
        y_offset = -self.c_form_width / 2
        axle_position = self.top_axle_position()
        x_offset1 = axle_position[0] - 40
        x_offset2 = axle_position[0] + 40
        z_offsets = [self.center_z + self.small_radius - 40 + self.top_bearing_extension_height + z for z in
                     [-45, -80, -115]]

        bolt = self.tools.hexagonal_bolt_hole_y(size="1/4", length=120)
        bolts = None
        for z in z_offsets:
            if not bolts:
                bolts = translate((x_offset1, y_offset, z))(bolt)
            else:
                bolts += translate((x_offset1, y_offset, z))(bolt)
            bolts += translate((x_offset2, y_offset, z))(bolt)
        return bolts

    def top_bearing_back_plate(self):
        name = "top_bearing_back_plate"
        axle_position = self.top_axle_position()
        back_plate = self.top_bearing_extension(self.top_bearing_tab_thickness * 2)

        back_plate = translate((0, self.top_bearing_tab_thickness + self.c_form_width / 2, 0))(back_plate)

        back_plate = difference()(
            back_plate(),
            translate((0, -self.top_bearing_body_gap, 0))(
                self.top_bearing_holder_shape(expand=self.top_bearing_body_gap, cutout=True)),
            translate((0, -200, 0))(cube((400, 400, axle_position[2] - 35))),

        )

        cutout = hull()(self.top_axle(8), translate((0, 0, 45))(self.top_axle(8)))
        cutout2 = hull()(translate((0, 0, -5))(self.top_axle(25)), translate((0, 0, 5))(self.top_axle(25)))

        back_plate -= cutout
        back_plate -= cutout2

        back_plate -= self.top_bearing_back_plate_bolts()

        return back_plate, name

    def top_bearing_holder_shape(self, expand=0.0, cutout=False, tension_bolt=False):
        # how far the tab is out of the body.
        tab_depth = self.top_bearing_tab_depth
        # the tab goes from the
        tab_width = self.c_form_width - self.top_bearing_tab_thickness
        object_height = self.top_bearing_holder_height
        tab_taper = 8
        z_offset = 0
        # if this is cutout of c_frame do not add taper to the side
        center_height = object_height
        body_depth_cut_to_allow_swing = 0
        if cutout:
            tab_taper = 0
            object_height += self.top_bearing_slide_capability + 5
            center_height = object_height + 100
            z_offset = 50
        else:
            body_depth_cut_to_allow_swing = tab_taper

        # we build the tab to place on the side.   It slopes in by tab_taper on both sides.
        tab = hull()(
            translate((0, -expand, 0.5))(cube((tab_depth + 2 * expand, tab_width + 2 * expand, 1), center=True)),
            translate((0, 0, object_height - 0.5))(
                cube((tab_depth + 2 * expand, (tab_width - 2 * tab_taper) + 2 * expand, 1), center=True)))
        tab = translate((0, 0, -object_height / 2))(tab)

        body_width = self.top_bearing_holder_width + expand * 2
        body_depth = self.c_form_width + self.top_bearing_tab_thickness - body_depth_cut_to_allow_swing / 2
        # we build the body of the bearing container
        shape = cube((body_width,
                      body_depth,
                      object_height), center=True)
        if cutout:
            center = cube((body_width,
                           15,  # bolts are 8 mm gives some wiggle room.
                           center_height), center=True)
            center = translate((0, 0, z_offset))(center)
            shape += center

        # we attach the tabs on the sides
        shape += translate((self.top_bearing_holder_width / 2 + tab_depth / 2, 0, 0))(tab)
        shape += translate((-(self.top_bearing_holder_width / 2 + tab_depth / 2), 0, 0))(tab)

        if tension_bolt:
            bolt = self.tools.hexagonal_bolt_hole_z(size="1/4", length=200)

            bolt_left = translate((11, 0, 0))(bolt)
            bolt_right = translate((-11, 0, 0))(bolt)

            bolts = bolt_right + bolt_left
            bolts = translate((0, 0, -self.top_bearing_holder_height / 2))(bolts)
            shape -= bolts

        # we compute the amount of y_shift necessary to put the object at the front of the c_frame
        y_shift = (body_depth) / 2 - self.c_form_width / 2
        shape = translate((0, 0, object_height / 2 - self.top_bearing_bottom_of_slot))(shape)
        shape = translate((self.center_x, y_shift, self.center_z + self.small_radius + 30))(shape)

        if cutout:
            shape = translate((0, 0, -5))(shape)
        return shape

    def top_wheel_axle_bearing_holder(self):
        name = "top_wheel_axle_bearing_holder"

        # cut out the bearing holder
        holder = self.top_bearing_holder_shape(tension_bolt=True)
        holder -= self.top_bearing(self.bearing_8mm_od, 14, )
        holder -= self.top_axle(9)

        holder -= translate((0, 0, self.top_bearing_holder_height - 45))(self.top_axle(8))
        bolt_position = self.top_axle_position()

        # cut out the holder for the alignment bolt head holder, this should be smaller than the axle
        # to allow wiggle room
        bolt = translate((bolt_position[0], -self.c_form_width / 2, bolt_position[2]))(
            self.tools.hexagonal_bolt_hole_y(size="1/4", length=50))
        bolt = translate((0, 0, self.top_bearing_holder_height - 45))(bolt)
        holder -= bolt
        printable = rotate((-90, 0, 0))(holder)

        return holder, name, printable

    def top_bearing_extension(self, thickness):
        radius = 25
        extension = hull()(
            translate((radius, 0, 0))(cylinder(r=radius, h=thickness, center=True)),
            translate((120 - radius, 0, 0))(cylinder(r=radius, h=thickness, center=True))
        )
        extension = rotate((90, 0, 0))(extension)

        extension = translate((0, 0, self.top_bearing_extension_height - 2 * radius))(extension)
        extension = hull()(extension,
                           translate((0, -thickness / 2, 0))(cube((120, thickness, 10)))
                           )

        extension = translate((self.center_x - 60, 0, self.center_z + self.small_radius - 40))(extension)
        return extension

    def test_wheels(self):
        name = "test_wheels"
        obj = self.c_form()[0]

        def cutter_filler(height):
            result = cube((100, self.c_form_width, height))
            result = translate((self.center_x - 50, -self.c_form_width / 2, 0))(result)
            return result

        cutter = cutter_filler(500)

        obj *= cutter
        filler = cutter_filler(80)
        obj += filler

        filler = cutter_filler(230)
        filler = translate((0, 0, 110))(filler)
        obj += filler

        return obj, name

    def cutter_tool_for_c_frame(self, angle):
        tool_x_center = self.center_x
        tool_y_center = self.center_z

        peg = cylinder(d=5, h=300, center=True) + cube((600, 2, 100), center=True)
        under_cutter = cube((600, 500, self.c_form_width / 2))
        under_cutter = translate((-300, 0, 0))(under_cutter)

        under_cutter = peg + under_cutter
        under_cutter = rotate((0, 0, angle))(under_cutter)
        under_cutter = translate((tool_x_center, tool_y_center, 0))(under_cutter)
        return under_cutter

    def c_form_250(self):
        name = "__SEGMENTS__"
        pieces = []

        main_c_form = self.c_form()[2]  # printable is aligned on the xy plane

        main_c_form = translate((0, -self.bottom_axle_position()[2] + 29, self.c_form_width / 2))(main_c_form)

        lower_x_top = 200
        lower_x_bottom = lower_x_top - self.c_form_width / 2

        lower_y = 100

        bottom_cutter = self.cutter_tool_for_c_frame(70)
        piece1 = union()(
            main_c_form,
            bottom_cutter)

        piece1 += translate((0, 0, -110))(bottom_cutter)
        piece1 = bottom_cutter
        piece2 = intersection()(
            main_c_form,
            translate((0, 200, 0))(cube((200, 200, 100)))
        )

        pieces = [dict(obj=piece1, name="c_form_300_part1", stl=True),
                  dict(obj=piece2, name="c_form_300_part2", stl=True),
                  dict(obj=piece1 + piece2, name="c_form_300_assembled_NO_PRINT", stl=False)
                  ]
        return pieces, name

    def c_form(self):
        name = "c_form"
        # make the ring for the darned thing
        c_form = self.big_circle_parametric(self.big_radius, self.c_form_width) - \
                 self.big_circle_parametric(self.small_radius, self.c_form_width)

        # now cut the ring in half
        c_form = c_form - translate((self.big_radius, -50, 0))(cube((400, 100, 600)))

        # add strengthener to the c_form to account for the slidy hole all the way through.
        c_form = c_form + intersection()(

            translate((self.center_x - self.small_radius, self.center_y, 0))(
                cube((self.c_form_brace_extension, self.c_form_width, 500))
            ),
            self.big_circle_parametric(self.big_radius, thickness=self.c_form_width)
        )

        # Cut out the entirey for the groove
        c_form = c_form - self.c_form_groove(top_angle=-45)

        # extend the bottom and the top forwards by 6 cm
        extension_length = 60  # from original design.
        extension_height = self.big_radius - self.small_radius

        # Add the bottom part
        c_form += translate((self.center_x, self.center_y, self.center_z - self.big_radius))(
            cube((extension_length, self.c_form_width, extension_height))
        )

        # Add the top part
        c_form += translate((self.center_x, self.center_y, self.center_z + self.small_radius))(
            cube((extension_length, self.c_form_width, extension_height))
        )

        c_form += self.top_bearing_extension(self.c_form_width)
        top_bearing_holder_cutter = self.top_bearing_holder_shape(expand=self.top_bearing_body_gap, cutout=True)
        c_form -= top_bearing_holder_cutter

        c_form -= self.guide_and_axle_cutout()

        # cut the holes out for the blade guides to bolt into.

        # top hole with nut slot
        z_offset = self.small_radius + extension_height / 2
        bolt_hole = translate((self.center_x + 60, 0, self.center_z + z_offset))(
            self.blade_guide_bolt_hole()
        )
        c_form -= bolt_hole

        # bottom hole with nut slot
        bolt_hole = translate((self.center_x + 60, 0, self.center_z - z_offset))(
            self.blade_guide_bolt_hole()
        )
        c_form -= bolt_hole

        c_form = c_form - self.bottom_bearing(self.bearing_8mm_od, 14)

        c_form = c_form - self.bottom_axle(9)

        c_form += self.blade_protector_extension()

        c_form -= self.blade_protector_bolts()

        c_form -= self.top_bearing_back_plate_bolts()

        printable = rotate((-90, 0, 0))(c_form)
        printable = translate((0, 0, self.c_form_width / 2))(printable)

        # Testing bolt stlo
        # c_form = self.top_bearing_holder_shape(expand=0.5, cutout=True)
        return c_form, name, printable

    def lower_bearing_test(self):
        name = "lower_bearing_test"
        x_cut = 30
        z_cut = 30
        c_form = self.c_form()[0]
        position = self.bottom_axle_position()
        cutter = cube((x_cut, 200, z_cut))
        cutter = translate((position[0] - x_cut / 2, -100, position[2] - z_cut / 2))(cutter)
        cut_form = intersection()(cutter, c_form)

        return cut_form, name

    def table_holder_slide_bolt_holes(self):
        center_x = self.back_plate_tip[0] - self.table_distance_from_tip - self.table_vertical_plate_width / 2
        x_offsets = [center_x + self.table_vertical_plate_width / 2 + 5,
                     center_x - self.table_vertical_plate_width / 2 - 5]

        z_offsets = [self.back_plate_tip[2] - 10,
                     self.back_plate_tip[2] - 60,
                     self.back_plate_tip[2] - 105]
        holes = None
        for x in x_offsets:
            for z in z_offsets:
                hole = translate((x, 0, z))(self.tools.hexagonal_bolt_hole_y(size="1/4", length=50))
                if holes:
                    holes += hole
                else:
                    holes = hole

        return holes

    def miter_hole_cutter(self, angle, radius):
        segments = 20 if self.production else 10
        hole = rotate((0, 0, angle))(
            translate((0, -radius, 0))(
                cylinder(h=30, d=self.tools.bolt_sizes["1/4"]["bolt"], center=True, segments=segments))
        )
        return hole

    def table_top_miter_rotation_slot(self):
        cut_steps = 10
        if self.production:
            cut_steps = 40

        angle_delta = 60 / cut_steps

        slot = self.miter_hole_cutter(0, self.table_top_miter_hole_offset)
        for i in range(1, cut_steps):
            slot += self.miter_hole_cutter(i * angle_delta, self.table_top_miter_hole_offset)
            slot += self.miter_hole_cutter(-i * angle_delta, self.table_top_miter_hole_offset)
        return slot

    def fence_bar_slot_maker(self, length=1000, epsilon=0):

        slot_depth = self.fence_guide_depth
        slot_depth_adjusted = self.fence_guide_depth - epsilon
        slot_height = slot_depth_adjusted * 3

        cutter = hull()(
            translate((0, 0, -slot_depth_adjusted / 2))(cube((length, 0.05, slot_depth_adjusted))),
            translate((0, -slot_depth_adjusted - epsilon, -slot_height / 2))(cube((length, 0.05, slot_height)))
        )
        offset = self.table_top_thickness / 2
        cutter = translate((0, slot_depth_adjusted, offset))(cutter)

        return cutter

    def total_table_depth(self):
        bar_depth = self.table_top_depth + self.back_plate_thickness + self.table_vertical_plate_thickness
        return bar_depth

    def fence_guard_attachment(self):

        attachment = cube((self.fence_attachment_width, self.fence_width, self.table_top_thickness))
        attachment += cube((self.fence_width, self.fence_width, self.table_top_thickness + self.fence_height))

        attachment += translate((0, self.fence_width, 0))(
            self.fence_bar_slot_maker(self.fence_attachment_width, 0.4))

        attachment -= self.fence_bar_bolt_holes()
        return attachment

        # attachment += translate((0,-bar_depth + self.fence_width, 0))(self.fence_bar_slot_maker(self.fence_attachment_width, 1))

    def fence_bar_attachment_front(self):
        name = "fence_bar_attachment_front"
        bar_depth = self.total_table_depth()

        attachment = self.fence_guard_attachment()
        printable = attachment
        attachment = translate((0, -bar_depth, 0))(attachment)

        attachment = self.translate_table_top_into_position(attachment)
        printable = rotate((90, 0, 0))(printable)
        return attachment, name, printable

    def fence_bar_attachment_back(self):
        name = "fence_bar_attachment_back"
        attachment = self.fence_guard_attachment()
        attachment = scale((1, -1, 1))(attachment)
        attachment = translate((0, self.fence_width, 0))(attachment)
        printable = attachment
        attachment = self.translate_table_top_into_position(printable)
        printable = rotate((-90, 0, 0))(printable)

        return attachment, name, printable

    def fence_bar_bolt_holes(self, for_fence=False):
        bolt = self.tools.round_bolt_hole_y("5mm", 1000)
        bolt = translate((0, -20, 0))(bolt)
        offset = 0
        if for_fence:
            offset = -500
        bolts = translate((self.fence_width / 2, offset, self.table_top_thickness + 15))(bolt)
        bolts += translate((self.fence_width / 2, offset, self.table_top_thickness + 40))(bolt)

        slot_diameter = self.tools.round_bolt_sizes["5mm"]["bolt"]

        cutter = rotate((90, 0, 0))(cylinder(d=slot_diameter, h=60, center=True))

        slot = hull()(translate((20, 0, self.table_top_thickness / 2))(cutter),
                      translate((self.fence_attachment_width - 20, 0, self.table_top_thickness / 2))(cutter))

        bolts += slot
        return bolts

    # Consistent placement of the nut holes for the fence in the table and in the fence
    def fence_nut_hole_depths(self, nut_width):
        return [-self.table_fence_nut_depth - nut_width / 2,
                -self.total_table_depth() + nut_width / 2 + self.table_fence_nut_depth]

    def fence_nut_holes(self):
        nut_width = self.tools.round_bolt_sizes["5mm"]["flat"]
        nut_depth = self.tools.round_bolt_sizes["5mm"]["depth"]
        nut_hole = cube((100, nut_depth, nut_width), center=True)
        nut_hole = translate((0, 0, 0))(nut_hole)
        y_offsets = self.fence_nut_hole_depths(nut_width)

        nut_holes = translate((self.fence_width / 2, y_offsets[0], self.table_top_thickness + 15))(nut_hole)
        nut_holes += translate((self.fence_width / 2, y_offsets[0], self.table_top_thickness + 40))(nut_hole)

        nut_hole = translate((0, y_offsets[1], 0))(nut_hole)
        nut_holes += translate((self.fence_width / 2, 0, self.table_top_thickness + 15))(nut_hole)
        nut_holes += translate((self.fence_width / 2, 0, self.table_top_thickness + 40))(nut_hole)

        return nut_holes

    def fence_nut_table_holes(self):
        nut_width = self.tools.round_bolt_sizes["5mm"]["flat"]
        nut_depth = self.tools.round_bolt_sizes["5mm"]["depth"]
        nut_hole = cube((nut_width, nut_depth, 100), center=True)
        nut_hole = translate((0, 0, 0))(nut_hole)
        y_offsets = self.fence_nut_hole_depths(nut_depth)

        nut_holes = translate((self.fence_attachment_width - 20, y_offsets[0], self.table_top_thickness / 2))(nut_hole)

        nut_holes += translate((self.fence_attachment_width - 20, y_offsets[1], self.table_top_thickness / 2))(nut_hole)

        return nut_holes

    def fence_bar(self):
        name = "fence_bar"

        bar_depth = self.total_table_depth()
        fence_bar = cube((self.fence_width, bar_depth, self.fence_height))
        fence_bar = translate((0, -bar_depth, self.table_top_thickness))(fence_bar)
        table_top = self.table_top()[2]
        front_attachment = self.fence_bar_attachment_front()[2]
        back_attachment = self.fence_bar_attachment_back()[2]

        printable = table_top + fence_bar + front_attachment + back_attachment

        fence_bar -= self.fence_bar_bolt_holes(True)

        fence_bar -= self.fence_nut_holes()
        printable = fence_bar

        fence_bar = self.translate_table_top_into_position(fence_bar)

        return fence_bar, name, printable

    def table_top_miter(self):
        name = "table_top_miter"

        big_segments = 100 if self.production else 30

        # make the base circle
        miter = cylinder(h=self.table_top_miter_thickness, r=self.table_top_miter_radius, segments=big_segments)

        # cut off the flat part at the front
        miter = miter - translate((-100, 0, -10))(cube((200, 200, 200)))

        # add the angle lines
        miter += self.miter_degree_lines()
        # cut out the rotation slot
        slot = self.table_top_miter_rotation_slot()
        miter -= slot

        # now do the prefixed holes
        set_angle_offset = self.table_top_miter_radius * self.table_top_miter_peg_offset_factor
        for angle in self.table_top_miter_set_angles:
            miter -= self.miter_angle_text(angle, str(angle), set_angle_offset - 10)
            miter -= self.miter_angle_text(-angle, str(angle), set_angle_offset - 10)
            miter -= self.miter_hole_cutter(angle, set_angle_offset)
            miter -= self.miter_hole_cutter(-angle, set_angle_offset)

        # build out the back
        back = cube(
            (self.table_top_miter_radius * 2, self.table_top_miter_back_plate_depth, self.table_top_miter_thickness))

        back_plate = cube((self.table_top_miter_radius * 2,
                           self.table_top_miter_back_plate_thickness,
                           self.table_top_miter_thickness * 3))
        back_plate = translate((0,
                                self.table_top_miter_back_plate_depth - self.table_top_miter_back_plate_thickness,
                                0))(back_plate)
        back += back_plate
        back = translate((-self.table_top_miter_radius, 0, 0))(back)

        miter += back

        miter -= self.miter_hole_cutter(0, 0)

        printable = miter
        miter = self.translate_miter_bar_to_position(miter)

        return miter, name, printable

    def miter_connect_holes(self):

        z_offset = self.table_miter_slot_depth
        center_hole = self.tools.hexagonal_bolt_hole_z("1/4", 50)
        center_hole = translate((0, 0, -z_offset))(center_hole)

        holder_hole = translate((0, -self.table_top_miter_hole_offset, 0))(center_hole)

        constant_hole = self.miter_hole_cutter(0, self.table_top_miter_radius * self.table_top_miter_peg_offset_factor)

        holes = center_hole + holder_hole + constant_hole
        return holes

    def miter_degree_lines(self):
        lines = None
        for i in range(71):
            line_length = 0
            if i % 5 == 0:
                line_length = 5
            if i % 10 == 0:
                line_length = 10
            if i in [30, 45]:
                line_length = 15
            if line_length == 0:
                continue
            line = cube((1, line_length, 1))
            line = translate((-.5, self.table_top_miter_radius - line_length - 1, self.table_top_miter_thickness))(line)
            line2 = rotate((0, 0, 180 - i))(line)
            line = rotate((0, 0, i + 180))(line)

            if not lines:
                lines = line2 + line
            else:
                lines += line2 + line
        return lines

    # make the guide for the pusher
    def table_top_miter_bar_maker(self, make_cutter):

        offset = 0.7  # this is because i made the cutter the default
        if make_cutter:
            offset = 1

        width = self.table_guide_slot_width + 2 * offset
        depth = self.table_miter_slot_depth
        bar = cube((width, 4000, depth), center=True)
        bar = translate((0, 0, -depth / 2))(bar)

        return bar

    def translate_miter_bar_to_position(self, object):
        result = translate((self.table_top_center_x + self.table_top_width / 2 - self.table_top_guide_offset,
                            self.table_top_center_y - self.table_vertical_plate_thickness - self.back_plate_thickness - 40,
                            self.table_top_center_z + self.table_top_thickness))(object)
        return result

    def translate_fence_bar_to_position(self, object):
        result = translate((self.table_top_center_x + self.table_top_width / 2 - self.table_top_guide_offset,
                            self.table_top_center_y - self.table_vertical_plate_thickness - self.back_plate_thickness - 40,
                            self.table_top_center_z + self.table_top_thickness))(object)
        return result

    def table_top_miter_bar(self):
        name = "table_top_miter_bar"
        guide_bar = self.table_top_miter_bar_maker(False)

        bar_length = self.table_top_guide_bar_length + self.back_plate_thickness + self.table_vertical_plate_thickness
        guide_bar = intersection()(
            cube((300, bar_length, 300), center=True),
            guide_bar)

        guide_bar = translate((0, -self.table_top_miter_radius, 0))(guide_bar)

        self.table_top_center_x = self.center_x + self.wheel_diameter / 2
        self.table_top_center_y = -self.c_form_width / 2 - self.wheel_offset_from_frame - (self.back_plate_thickness)
        self.table_top_center_z = self.back_plate_tip[2]

        guide_bar = translate((0, bar_length / 2, 0))(guide_bar)

        guide_bar -= self.miter_connect_holes()
        printable = guide_bar
        guide_bar = self.translate_miter_bar_to_position(guide_bar)

        return guide_bar, name, printable

    def miter_angle_text(self, angle, label, offset):
        text_result = linear_extrude(2)(text(label, halign="center", size=5))
        text_result = translate((0, 0, self.table_top_miter_thickness - 2))(text_result)
        text_result = rotate((0, 0, angle + 180))(translate((0, offset, 0))(text_result))
        return text_result

    def table_slider_holder_panel(self):
        name = "table_slider_holder_panel"

        slider_holder = self.table_holder_slide(self.table_vertical_plate_thickness, self.table_slide_holder_width,
                                                self.back_plate_height,
                                                self.table_vertical_plate_width)

        y_extra = .5  # to accomodate for how we build the slides with cylinders of d = 0.5
        bottom_height = self.back_plate_height - self.table_vertical_plate_height - 5  # leave a gap for cleaning sawdust
        bottom_cube = cube((self.table_vertical_plate_width + 2 * self.table_slide_holder_width,
                            self.table_vertical_plate_thickness + y_extra, bottom_height))
        bottom_cube = translate(
            (self.back_plate_tip[0] - self.table_distance_from_tip - self.table_vertical_plate_width,
             self.c_form_width / 2 + self.back_plate_thickness - y_extra / 2,
             0))(bottom_cube)
        slider_holder += bottom_cube

        slider_holder -= self.side_sub_base_connector_bolt_holes()
        # slide_holder -= translate((250,0,0))(cube((200,100,140)))

        # cut out the holes for the bolts that hold the slider holder to the back frame
        slider_holder -= translate((0, 30, 0))(self.table_holder_slide_bolt_holes())
        slider_holder = intersection()(self.base_back_plate_solid(100), slider_holder)
        slider_holder -= self.bottom_axle(self.bottom_axle_access_diameter)
        printable = rotate((90, 0, 0))(slider_holder)
        return slider_holder, name, printable

    def table_holder_slide(self, thickness, width, height, separation, epsilon=0.5):
        right = hull()(
            translate((0, 0, 0))(cylinder(d=0.5, h=height)),
            translate((width + thickness / 2, 0, 0))(cylinder(d=0.5, h=height)),
            translate((width, thickness / 2, 0))(cylinder(d=0.5, h=height)),
            translate((0, thickness / 2, 0))(cylinder(d=0.5, h=height))
        )
        outer_right = hull()(
            translate((0, 0, 0))(cylinder(d=0.5, h=height)),
            translate((width, 0, 0))(cylinder(d=0.5, h=height)),
            translate((width + thickness / 2, thickness / 2, 0))(cylinder(d=0.5, h=height)),
            translate((0, thickness / 2, 0))(cylinder(d=0.5, h=height))
        )
        right += translate((0, thickness / 2, 0))(outer_right)
        left = scale((-1, 1, 1))(right)
        right = translate((-width - epsilon, 0, 0))(right)

        left = translate((separation + width + epsilon, 0, 0))(left)

        bridge = translate((-width - epsilon, thickness, 0))(cube((2 * width + separation + 2 * epsilon, 5, 60)))

        slides = left + right

        slides = translate((self.back_plate_tip[0] - self.table_distance_from_tip - self.table_vertical_plate_width,
                            self.c_form_width / 2 + self.back_plate_thickness,
                            self.back_plate_tip[2] - height))(slides)

        holes = self.table_holder_slide_bolt_holes()
        slides -= holes
        return slides

    def table_top(self):
        name = "table_top"

        # first lets make the table
        # Calculate how much deeper to make the table
        table_extra_depth = self.back_plate_thickness + self.table_vertical_plate_thickness
        table_depth = self.table_top_depth + table_extra_depth

        table_width = self.table_top_width
        # use the hull operator on cylinders to make it nice with round corners
        table_top = hull()(
            translate((self.table_top_corner_radius, self.table_top_corner_radius, 0))(cylinder(
                r=self.table_top_corner_radius, h=self.table_top_thickness)),
            translate((table_width - self.table_top_corner_radius, self.table_top_corner_radius, 0))(cylinder(
                r=self.table_top_corner_radius, h=self.table_top_thickness)),
            translate((table_width - self.table_top_corner_radius, table_depth - self.table_top_corner_radius, 0))(
                cylinder(
                    r=self.table_top_corner_radius, h=self.table_top_thickness)),
            translate((self.table_top_corner_radius, table_depth - self.table_top_corner_radius, 0))(cylinder(
                r=self.table_top_corner_radius, h=self.table_top_thickness))
        )

        # translated the table by the half of the back end of the table_depth

        table_top = translate((0,
                               -table_extra_depth / 2,
                               0))(table_top)

        center_hole_x = self.table_top_width / 2
        center_hole_y = self.table_top_depth / 2 + self.wheel_offset_from_frame

        # cut out the center hole for the center of the table, it is square or a cylinder
        # depending on the value of self.make_center_hole_square
        if self.make_center_hole_square:
            # calculate the origin of the square
            x_origin = center_hole_x - self.table_top_cutout_diameter / 2
            y_origin = center_hole_y - self.table_top_cutout_diameter / 2
            # calculate the origin offset by self.table_top_cutout_extra
            x_origin_offset = x_origin - self.table_top_cutout_extra
            y_origin_offset = y_origin - self.table_top_cutout_extra
            # calculate the width of the main square
            square_width = self.table_top_cutout_diameter
            # calculate the width of the top square
            square_top_width = self.table_top_cutout_diameter + 2 * self.table_top_cutout_extra
            # calculate the z_offset of the top square
            z_offset = self.table_top_thickness - self.table_top_cutout_depth
            # make the main square

            center_hole = translate((x_origin, y_origin, 0))(cube((square_width, square_width, z_offset)))
            # make the bottom square
            center_hole += translate((x_origin_offset, y_origin_offset, z_offset))(
                cube((square_top_width, square_top_width, 40)))
        else:
            center_hole = cylinder(d=self.table_top_cutout_diameter, h=100, center=True)
            center_hole += translate((0, 0, self.table_top_thickness - self.table_top_cutout_depth))(
                cylinder(d=self.table_top_cutout_diameter + 2 * self.table_top_cutout_extra, h=20))
            center_hole = translate((center_hole_x, center_hole_y, 0))(
                center_hole)
        table_top -= center_hole

        center_cut = translate((self.table_top_width / 2 - 1, -100, 0))(
            cube((2, self.table_top_depth / 2 + 100, self.table_top_thickness)))

        table_top -= center_cut
        table_top -= self.table_fence_guard_bolt()
        # move the table so it is completely in front of the y axix

        printable = translate((0, table_extra_depth / 2, 0))(table_top)

        guide_slot = self.table_top_miter_bar_maker(True)
        printable = printable - translate(
            (self.table_top_width - self.table_top_guide_offset, 0, self.table_top_thickness))(guide_slot)

        printable = translate((0, - table_depth, 0))(printable)
        printable -= translate((0, -table_depth, 0))(self.fence_bar_slot_maker())
        printable -= scale((1, -1, 1))(self.fence_bar_slot_maker())
        printable -= self.fence_nut_table_holes()

        table_top = self.translate_table_top_into_position(printable)

        table_top -= self.table_attachment_bolts()
        printable = self.translate_table_top_into_position(table_top, inverse=True)

        return table_top, name, printable

    def table_fence_guard_bolt(self):
        bolt_offset_x = self.fence_attachment_width - 20
        bolt_offset_z = self.table_top_thickness / 2
        bolt_diameter = self.tools.round_bolt_sizes["5mm"]["bolt"]

        bolt_cutter = rotate((90, 0, 0))(cylinder(d=bolt_diameter, h=1000, center=True))
        bolt_cutter = translate((bolt_offset_x, 0, bolt_offset_z))(bolt_cutter)
        return bolt_cutter

    def translate_table_top_into_position(self, object, inverse=False):
        # move the table top into position
        table_extra_depth = self.back_plate_thickness + self.table_vertical_plate_thickness
        table_top_height = self.back_plate_tip[2]
        table_top_center_x = self.center_x + self.wheel_diameter / 2  # the hole is centered on the blade
        # table_top_center_x = self.bottom_axle_position()[0]
        table_top_y_position = self.c_form_width / 2 + table_extra_depth
        x_translate = table_top_center_x - self.table_top_width / 2
        y_translate = table_top_y_position
        z_translate = table_top_height
        if inverse:
            translated_object = translate((-x_translate, -y_translate, -z_translate))(object)
        else:
            translated_object = translate((x_translate, y_translate, z_translate))(object)
        return translated_object

    def table_attachment_bolts(self):
        bolt = self.tools.round_bolt_hole_z("5mm", 200)
        bolt = scale((1, 1, -1))(bolt)

        # cut out the slot for the nut
        # adjusted for the printer
        slot_width = self.tools.bolt_sizes["5mm"]["flat"]
        slot_depth = 100
        slot_height = self.tools.bolt_sizes["5mm"]["depth"]
        slot = translate((0, 0, -70 + slot_height / 2))(cube((slot_width, slot_depth, slot_height), center=True))
        bolt += slot

        bolt = translate(self.back_plate_tip)(bolt)
        bolt = translate((-self.table_vertical_plate_width - self.table_distance_from_tip,
                          self.table_vertical_plate_thickness / 2, self.table_top_thickness))(bolt)

        bolts = translate((self.table_vertical_plate_width / 4, 0, 0))(bolt)
        bolts += translate((self.table_vertical_plate_width / 2, 0, 0))(bolt)
        bolts += translate((self.table_vertical_plate_width * 3 / 4, 0, 0))(bolt)
        return bolts

    def table_slider_attachment(self):
        name = "table_slider_attachment"

        table_attachment = cube((self.table_vertical_plate_width,
                                 self.table_vertical_plate_thickness, self.table_vertical_plate_height))

        x_offsets = [self.table_vertical_plate_width / 2 - self.table_connector_bolt_separation / 2,
                     self.table_vertical_plate_width / 2 + self.table_connector_bolt_separation / 2]

        adjustment_groove = hull()(
            translate((0, 0, self.table_vertical_plate_height - 20))(
                self.tools.horizontal_cylinder_d(d=self.guide_small_groove, h=200, center=True)
            ),
            translate((0, 0, 10))(
                self.tools.horizontal_cylinder_d(d=self.guide_small_groove, h=200, center=True)
            )
        )

        table_attachment -= translate((x_offsets[1], self.table_vertical_plate_thickness - 5, 0))((adjustment_groove))
        table_attachment -= translate((x_offsets[0], self.table_vertical_plate_thickness - 5, 0))((adjustment_groove))

        # move the table attachment into place
        table_attachment = translate(self.back_plate_tip)(table_attachment)

        table_attachment = translate((-self.table_vertical_plate_width - self.table_distance_from_tip,
                                      0, -self.table_vertical_plate_height))(
            table_attachment
        )

        # Now trim the slides off to make the slider.
        slides = self.table_holder_slide(self.table_vertical_plate_thickness, self.table_slide_holder_width,
                                         self.table_vertical_plate_height * 2,
                                         self.table_vertical_plate_width, epsilon=0)
        table_attachment -= translate((0, 0, 10))(slides)

        # table_attachment += translate((0,-40,0))(self.table_top()[0])
        # Now make the grooves for the bolt holes.
        bolts = self.table_attachment_bolts()
        table_attachment -= bolts
        printable = table_attachment
        printable = translate((self.table_vertical_plate_width + self.table_distance_from_tip,
                               0, self.table_vertical_plate_height))(printable)
        printable = rotate((90, 0, 0))(printable)

        return table_attachment, name, printable

    def blade_guide_bolt_hole(self):
        depth = 30
        bolt_hole = rotate((0, 0, 90))(
            self.tools.horizontal_cylinder_d(d=6.6, h=depth + 20, center=False)
        )
        nut_slot = translate((-depth, -100, -5))(
            cube((5.2, 200, 10.3))
        )
        return bolt_hole + nut_slot

    def bottom_axle_position(self):
        return (self.center_x, self.center_y - self.wheel_thickness / 2 - self.wheel_offset_from_frame,
                self.center_z - 185 + 29)

    def top_axle_position(self):
        return (self.center_x, self.center_y - self.wheel_thickness / 2 - self.wheel_offset_from_frame,
                self.center_z + 185 - 29)

    def bottom_bearing(self, diameter, height):
        segments = 15
        if self.production:
            segments = 30
        position = list(self.bottom_axle_position())
        position[1] = -self.c_form_width / 2
        axle = translate(position)(
            rotate((-90, 0, 0))(
                cylinder(d=diameter, h=height, segments=segments)
            )
        )
        # now put the bearing hole at the back
        back_y_position = self.c_form_width / 2 - height
        axle += translate((position[0], back_y_position, position[2]))(
            rotate((-90, 0, 0))(
                cylinder(d=diameter, h=height, segments=segments)
            )
        )
        # Now put an angle at the back to make it print with no supports
        back_y_position -= 7
        axle += translate((position[0], back_y_position, position[2]))(
            rotate((-90, 0, 0))(
                cylinder(d2=diameter, d1=diameter - 14, h=7, segments=30)
            )
        )
        return axle

    def top_bearing(self, diameter, height):
        position = list(self.top_axle_position())
        position[1] = -self.c_form_width / 2
        axle = translate(position)(
            rotate((-90, 0, 0))(
                cylinder(d=diameter, h=height, segments=30)
            )
        )

        back_y_offset = 2  # to account for this part being smaller than the c_frame_widht
        # now put the bearing hole at the back
        back_y_position = self.c_form_width / 2 + self.top_bearing_tab_thickness - height - back_y_offset
        axle += translate((position[0], back_y_position, position[2]))(
            rotate((-90, 0, 0))(
                cylinder(d=diameter, h=height, segments=30)
            )
        )
        # Now put an angle at the back to make it print with no supports
        back_y_position -= 7
        axle += translate((position[0], back_y_position, position[2]))(
            rotate((-90, 0, 0))(
                cylinder(d2=diameter, d1=diameter - 14, h=7, segments=30)
            )
        )
        return axle

    def bottom_axle(self, diameter):
        axle = translate(self.bottom_axle_position())(
            rotate((-90, 0, 0))(
                cylinder(d=diameter, h=1000, center=True, segments=30)
            )
        )
        return axle

    def top_axle(self, diameter):
        axle = translate(self.top_axle_position())(
            rotate((-90, 0, 0))(
                cylinder(d=diameter, h=1000, center=True, segments=30)
            )
        )
        return axle

    def inner_slider(self):
        epsilon = 0.5
        small_diameter = 142 + epsilon
        large_diameter = 168 - epsilon

        slider = self.c_form_groove(top_angle=-100, bottom_angle=30,
                                    small_diameter=small_diameter, large_diameter=large_diameter)
        return slider

    def axle_cutout_for_back_plate(self):
        small_diameter = 142
        large_diameter = 168

        slider = self.c_form_groove(top_angle=180, bottom_angle=310,
                                    small_diameter=small_diameter, large_diameter=large_diameter)
        return slider

    def test_bolts_bar(self):
        name = "test_bolt_bar"

        hex_test = ["1/4", "4mm"]
        round_test = ["5mm", "4mm"]
        number_of_bolts = max(len(hex_test), len(round_test))
        bolt_sample = 20
        length_of_sample = number_of_bolts * bolt_sample
        obj = translate((0, 0, -12))(cube((length_of_sample, 50, 12)))
        i = 0
        for key in hex_test:
            bolt = self.tools.hexagonal_bolt_hole_z(size=key, length=40)
            obj -= translate((10 + i * 20, 10, 0))(rotate((0, 180, 0))(bolt))
            obj -= translate((10 + i * 20, 18, -1))(linear_extrude(height=3)
                                                    (text(key, 5, halign="center")))
            print("hex->[{}]".format(key))

            i += 1

        i = 0
        for key in round_test:
            bolt = self.tools.round_bolt_hole_z(size=key, length=40)
            obj -= translate((10 + i * 20, 30, 0))(rotate((0, 180, 0))(bolt))
            obj -= translate((10 + i * 20, 38, -1))(linear_extrude(height=3)
                                                    (text(key, 5, halign="center")))
            print("hex->[{}]".format(key))
            print("rnd->[{}]".format(key))
            i += 1
        obj = (obj)
        return obj, name

    def table_connector_bolt_holes(self):
        center_x = self.back_plate_tip[0] - self.table_distance_from_tip - self.table_vertical_plate_width / 2
        center_y = self.c_form_width / 2
        center_z = self.back_plate_tip[2] - 20

        holes = translate((center_x - self.table_connector_bolt_separation / 2, center_y, center_z))(
            self.tools.hexagonal_bolt_hole_y(size="1/4", length=200))
        holes += translate((center_x + self.table_connector_bolt_separation / 2, center_y, center_z))(
            self.tools.hexagonal_bolt_hole_y(size="1/4", length=200))
        return holes

    def test_wheel_connection(self):
        name = "test_wheel_connection"
        wheel = self.wheel(True)
        wheel = rotate((-90, 0, 0))(wheel)
        wheel = intersection()(wheel, cylinder(d=40, h=200, center=True))
        return wheel, name

    def wheel_flat(self):
        segments = 20
        if self.production:
            segments = 300
        wheel = self.tools.horizontal_cylinder_d(d=self.wheel_diameter, h=self.wheel_thickness, segments=segments)
        wheel = translate((0, -self.wheel_thickness / 2.0))(wheel)
        return wheel

    def wheel_crowned(self, top=True):
        axle = 12
        radius = self.wheel_diameter / 2
        half_width = self.wheel_thickness / 2

        center = 40  ## 100
        if not top:
            center = 100 #bottom wheel has a slight arch
        offset = radius - center

        slivers = 5
        segments = 20
        if self.production:
            slivers = 20
            segments = 300

        delta = half_width / (slivers - 1)

        def radius(center, offset, x):
            y = math.sqrt(center * center - x * x)
            y += offset
            return y

        radii = []
        for i in range(slivers):
            radii.append(radius(center, offset, i * delta))

        wheel = self.tools.horizontal_cylinder_d1d2(d1=radii[0] * 2, d2=radii[1] * 2, h=delta, segments=segments)
        wheel += scale((1, -1, 1))(wheel)
        for i in range(slivers - 2):
            j = i + 1
            sliver = self.tools.horizontal_cylinder_d1d2(d1=radii[j] * 2, d2=radii[j + 1] * 2, h=delta,
                                                         segments=segments)
            sliver = translate((0, j * delta, 0))(sliver)
            sliver += scale((1, -1, 1))(sliver)
            wheel += sliver
        return wheel

    def wheel(self, top, cutout=True):

        wheel = self.wheel_crowned(top)
        wheel = difference()(
            wheel,
            translate((0, 0, 0))(self.tools.hexagonal_bolt_hole_y(size="8mm-rod", length=300, make_head=False))
        )

        # now the holes for the nuts that will hold the wheel to the collet

        coupling_holes = translate((0, 0, -self.wheel_thickness / 2))(cylinder(d=32.6, h=6, segments=30))
        for angle in [0, 90, 180, 270]:
            hole = rotate((0, 0, angle))(
                translate((12.1, 0, 0))(
                    cylinder(d=self.tools.bolt_sizes["4mm"]["bolt"], h=100, center=True, segments=20)
                ))
            if coupling_holes:
                coupling_holes += hole
            else:
                coupling_holes = hole
        coupling_holes = rotate((90, 0, 0))(coupling_holes)
        coupling_holes = rotate((0, 45, 0))(coupling_holes)
        wheel -= coupling_holes

        if cutout:
            # cut out the holes in the wheel
            offset = 40
            hole_diameter = 40
            wheel -= translate((offset, 0, 0))(self.tools.horizontal_cylinder_d(d=hole_diameter, h=200, center=True))
            wheel -= translate((-offset, 0, 0))(self.tools.horizontal_cylinder_d(d=hole_diameter, h=200, center=True))
            wheel -= translate((0, 0, offset))(self.tools.horizontal_cylinder_d(d=hole_diameter, h=200, center=True))
            wheel -= translate((0, 0, -offset))(self.tools.horizontal_cylinder_d(d=hole_diameter, h=200, center=True))

        return wheel

    def blade(self):
        blade_depth = 5
        bottom_axle_pos = self.bottom_axle_position()
        top_axle_pos = self.top_axle_position()
        length = top_axle_pos[2] - bottom_axle_pos[2]
        y_position = -self.wheel_thickness / 2 - self.c_form_width / 2 - self.wheel_offset_from_frame - blade_depth / 2
        blade = translate((bottom_axle_pos[0], y_position, bottom_axle_pos[2]))(
            translate((self.wheel_diameter / 2, 0, 0))(
                cube((1, blade_depth, length))
            )
        )
        blade += translate((bottom_axle_pos[0], y_position, bottom_axle_pos[2]))(
            translate((-self.wheel_diameter / 2 - 1, 0, 0))(
                cube((1, blade_depth, length))
            )
        )
        return blade

    def bottom_wheel(self):
        name = "bottom_wheel"
        bottom_wheel = self.wheel(top=False)
        printable = rotate((90, 0, 0))(bottom_wheel)
        bottom_wheel = translate(self.bottom_axle_position())(bottom_wheel)
        return bottom_wheel, name, printable

    def top_wheel(self):
        name = "top_wheel"
        printable = rotate((90, 0, 0))(self.wheel(top=True))
        top_wheel = translate(self.top_axle_position())(printable)
        return top_wheel, name, printable

    def blade_guide_shape(self, height):
        # the plate
        plate = translate((0, -self.c_form_width / 2, 0))(
            cube([self.guide_plate_thickness, self.c_form_width, height]))
        # the part that sits in the c_frame.
        tongue_tip = translate((-self.guide_tongue_thickness, -self.guide_tongue_width / 2, 0))(
            cube((self.guide_tongue_thickness, self.guide_tongue_width, height)))
        tongue_width = self.c_form_width - 8
        tongue_base = translate((0, -tongue_width / 2, 0))(
            cube([self.guide_plate_thickness, tongue_width, height]))
        tongue = hull()(tongue_base, tongue_tip)
        guide = plate + tongue

        return guide

    def blade_guide(self, height):

        # the plate
        guide = self.blade_guide_shape(height)
        # the groove to allow this piece to move up and down.
        adjustment_groove = rotate((0, 0, -90))(
            hull()(
                translate((0, 0, height - self.guide_groove_from_top))(
                    self.tools.horizontal_cylinder_d(d=self.guide_small_groove, h=200, center=True)
                ),
                translate((0, 0, self.guide_groove_from_bottom))(
                    self.tools.horizontal_cylinder_d(d=self.guide_small_groove, h=200, center=True)
                )
            )
        )

        # the slot for the head of the bolt.
        big_groove = rotate((0, 0, -90))(
            hull()(
                translate((0, 0, height - self.guide_groove_from_top))(
                    self.tools.horizontal_cylinder_d(d=self.guide_large_groove, h=200, center=False)
                ),
                translate((0, 0, self.guide_groove_from_bottom))(
                    self.tools.horizontal_cylinder_d(d=self.guide_large_groove, h=200, center=False)
                )
            )
        )
        adjustment_groove += translate((self.guide_large_groove_depth, 0, 0))(big_groove)
        guide -= adjustment_groove

        # now cut out the holder for the metal part that will hold the bearings for the guide.
        self.bearing_plate_height = 30
        self.bearing_plate_depth = 6

        bearing_plate_cutter = cube((self.bearing_plate_depth, self.c_form_width, self.bearing_plate_height))
        bearing_plate_cutter = translate(
            (self.guide_plate_thickness - self.bearing_plate_depth, -self.c_form_width / 2, 0))(bearing_plate_cutter)

        guide -= bearing_plate_cutter

        plate_holder_holes = self.plate_holder_holes()
        guide -= plate_holder_holes
        return guide

    def top_blade_guide(self):
        name = "top_blade_guide"
        guide = self.blade_guide(self.guide_plate_top_height)
        guide = translate((self.center_x + 60, 0, self.center_z + self.big_radius - self.guide_plate_top_height))(guide)
        return guide, name

    def thrust_bearing_hole(self):
        y_offsets = [-self.c_form_width / 4, self.c_form_width / 4]

        def hole():
            hole = rotate((0, 0, 90))(
                self.tools.horizontal_cylinder_d(d=self.guide_plate_bolt_diameter, h=100, center=True)
            )
            return hole

        slot = hull()(
            translate((0, 7, 11))(hole()),
            translate((0, 15, 11))(hole())
        )
        return slot

    def guide_bearing_slots(self):
        z_offset = -7
        slot_depth = 10
        screw_depth = 32
        slots = hull()(
            translate((-22, -screw_depth, z_offset))(
                self.tools.horizontal_cylinder_d(d=4.4, h=screw_depth, segments=4)),
            translate((12, -screw_depth, z_offset))(self.tools.horizontal_cylinder_d(d=4.4, h=screw_depth, segments=4))
        )

        slots += hull()(
            translate((-100, 0, z_offset))(self.tools.horizontal_cylinder_d(d=7.7, h=slot_depth, center=False)),
            translate((100, 0, z_offset))(self.tools.horizontal_cylinder_d(d=7.7, h=slot_depth, center=False))
        )

        slots = translate((0, 20, 0))(slots)
        return slots

    def blade_guide_bearing_holder(self):

        self.bearing_holder_height = 30
        self.bearing_holder_extension = 3  # how much towards the front we need to push bearings
        self.bearing_holder_front_length = 16
        self.bearing_holder_slope_length = 16  # could link with the above
        self.bearing_holder_front_slope_height = 17
        self.bearing_holder_length = self.c_form_width + self.bearing_holder_front_length
        self.bearing_holder_thickness = 18

        constructor_cube = cube((self.bearing_holder_thickness, 1, 1))
        # The shape of the holder according to the original plan
        obj = hull()(
            translate(
                (0, self.bearing_holder_slope_length - self.bearing_holder_extension, self.bearing_holder_height - 1))(
                constructor_cube),
            translate((0, self.bearing_holder_length - 1, self.bearing_holder_height - 1))(constructor_cube),
            translate((0, self.bearing_holder_length - 1, 0))(constructor_cube),
            translate((0, -self.bearing_holder_extension, 0))(constructor_cube),
            translate((0, -self.bearing_holder_extension, self.bearing_holder_front_slope_height))(
                constructor_cube)
        )

        # cut out the holes
        hole_cutter = translate((0, -self.center_y + self.bearing_holder_front_length, 0))(
            self.plate_holder_holes(make_slot=True)
        )
        obj -= hole_cutter

        # cut out the slot for the thrust bearing
        obj -= translate((0, -self.bearing_holder_extension, 0))(self.thrust_bearing_hole())

        # build out the holder for the guide bearings.
        obj += translate((-28, 5 - self.bearing_holder_extension, -15))(cube((46, 19, 15)))

        obj -= translate((0, -self.bearing_holder_extension, 0))(self.guide_bearing_slots())

        return obj

    # The throttle controller the part you put on your drill to control the throttle

    def throttle_controller(self):
        name = "__SEGMENTS__"
        drill_handle_width = 37
        drill_handle_length = 45
        base_height = 14
        base_wall_thickness = 15
        pusher_thickness = 20
        handle_width = 10
        axle_offset = 47
        controller_handle_length = 60
        controller_handle_angle = 150

        drill_cutter = hull()(
            cylinder(d=drill_handle_width, h=100, center=True),
            translate((drill_handle_length - drill_handle_width, 0, 0))(
                cylinder(d=drill_handle_width, h=100, center=True))
        )
        cut_width = drill_handle_width + 2
        drill_cutter = translate((-(drill_handle_length - drill_handle_width) / 2, 0, 0))(drill_cutter)
        drill_cutter += translate((-cut_width / 2, 0, -50))(cube((cut_width, 100, 100)))

        base_body = hull()(
            cylinder(d=drill_handle_width + 2 * base_wall_thickness, h=base_height),
            translate((drill_handle_length - drill_handle_width + axle_offset, 0, 0))(
                cylinder(d=drill_handle_width + 2 * base_wall_thickness, h=base_height))
        )
        base = base_body - translate((axle_offset, 0, 0))(drill_cutter)

        bolt_hole = self.tools.hexagonal_bolt_hole_z("1/4", 50)
        controller_pusher = cylinder(d=30, h=pusher_thickness)

        controller_handle = translate((controller_handle_length / 2, 0, handle_width / 2))(
            cube((controller_handle_length, handle_width, handle_width), center=True))
        controller_handle = rotate((0, 0, controller_handle_angle))(controller_handle)

        controller_base = cylinder(d=50, h=5)
        controller = controller_pusher + controller_handle
        controller = translate((-10, 0, 0))(controller)

        controller = translate((0, 0, base_height))(controller)
        controller -= bolt_hole

        attachment_bolt = self.tools.hexagonal_bolt_hole_x("1/4", 100)
        attachment_bolt = rotate((30, 0, 0))(attachment_bolt)
        attachment_bolt = translate((axle_offset + drill_handle_width / 2 + 7, 0, base_height / 2))(attachment_bolt)
        attachment_bolt = difference()(attachment_bolt, cube((100, 100, 100), center=True))
        base -= attachment_bolt

        attachment_bolt = rotate((0, 0, -90))(attachment_bolt)
        attachment_bolt = translate((axle_offset, axle_offset + 4, 0))(attachment_bolt)
        base -= attachment_bolt

        base = translate((0, -10, 0))(base)
        base -= bolt_hole

        pieces = [dict(obj=controller, name="speed_controller", stl=True),
                  dict(obj=base, name="speed_controller_harness", stl=True),
                  dict(obj=controller + base, name="controller_NO_PRINT", stl=False)
                  ]
        return pieces, name
        result = base + controller_pusher
        # result = drill_cutter
        return pieces, name

    def blade_guide_bearing_bolt_v2(self):
        bolt = self.tools.round_bolt_hole_z("4mm", length=50)
        bolt = scale((1, 1, -1))(bolt)
        bolt = translate((self.bearing_holder_front_length - self.bearing_holder_thickness / 2, self.c_form_width - 3,
                          self.bearing_holder_height))(bolt)
        return bolt

    # This was never finished.  The intention here was to make a bearing holder
    # that would allow the thrust bearing to be mounted with a bolt and the nut
    # would be recessed into the holder.  This was never finished.

    def blade_guide_bearing_holder_v2(self):
        name = "blade_guide_bearing_holder_v2"

        self.bearing_holder_height = 30
        self.bearing_holder_extension = 3  # how much towards the front we need to push bearings
        self.bearing_holder_front_length = 16
        self.bearing_holder_slope_length = 16  # could link with the above
        self.bearing_holder_front_slope_height = 17
        self.bearing_holder_length = self.c_form_width + self.bearing_holder_front_length
        self.bearing_holder_thickness = 18
        self.guide_bearing_x_offset = 28

        self.thrust_bearing_thickness = 15

        obj = cube((self.bearing_holder_thickness, self.c_form_width, self.bearing_holder_height))
        obj = translate((0, self.bearing_holder_front_length, 0))(obj)

        connector = obj

        thrust_bearing_holder = cube((self.thrust_bearing_thickness, self.bearing_holder_front_length + 5,
                                      self.bearing_holder_front_slope_height))
        thrust_bearing_holder = translate((0, 0, 0))(thrust_bearing_holder)

        thrust_bearing_holder = translate((-self.guide_bearing_x_offset, 0, 0))(thrust_bearing_holder)
        thrust_bearing_holder -= self.thrust_bearing_hole()

        # cut out the holes
        connector -= translate((0, -self.center_y + self.bearing_holder_front_length, 0))(
            self.plate_holder_holes(make_slot=True)
        )

        # build out the holder for the guide bearings.
        guide_bearing_holder = translate((-self.guide_bearing_x_offset,
                                          self.bearing_holder_extension - self.bearing_holder_extension,
                                          -15))(cube((46, self.bearing_holder_front_length + self.c_form_width, 15)))

        guide_bearing_holder -= translate((0, -self.bearing_holder_extension, 0))(self.guide_bearing_slots())

        bearing_holder = guide_bearing_holder + thrust_bearing_holder
        connector_bolt = self.blade_guide_bearing_bolt_v2()

        connector -= connector_bolt
        bearing_holder -= connector_bolt
        name = "__SEGMENTS__"
        pieces = [dict(obj=connector, name="bearing_connector", stl=True),
                  dict(obj=bearing_holder, name="bearing_connector_foot", stl=True),
                  dict(obj=connector + translate((0, 0, -10))(bearing_holder), name="bearing_connector_assembled",
                       stl=False)
                  ]

        return pieces, name

    def upper_blade_guide_bearing_holder(self):
        name = "upper_blade_guide_bearing_holder"
        obj = self.blade_guide_bearing_holder()

        # make the printable copy
        printable = obj
        printable = rotate((0, 90, 0))(printable)

        # place the object in the right place.
        obj = translate((self.center_x + 60 + 16, self.center_y - 16,
                         self.center_z + self.big_radius - self.guide_plate_top_height))(obj)

        return obj, name, printable

    def lower_blade_guide_bearing_holder(self):
        name = "lower_blade_guide_bearing_holder"
        obj = self.blade_guide_bearing_holder()
        obj = scale((1, 1, -1))(obj)

        # make the printable object
        printable = obj
        printable = rotate((0, 90, 0))(printable)

        # place the object in the right place.
        obj = translate((self.center_x + 60 + 16, self.center_y - 16,
                         self.center_z - 100))(obj)
        return obj, name, printable

    def bottom_blade_guide(self):
        name = "bottom_blade_guide"
        guide = self.blade_guide(self.guide_plate_bottom_height)
        guide = scale((1, 1, -1))(guide)
        guide = translate((self.center_x + 60, 0, self.center_z - 100))(guide)
        return guide, name

    def plate_holder_holes(self, make_slot=False):
        y_offsets = [-self.c_form_width / 4, self.c_form_width / 4]
        z_offsets = [10, 20]
        slot_offset = 0
        if make_slot:
            slot_offset = [-2, 6]

        def hole():

            result = rotate((0, 0, 90))(
                self.tools.horizontal_cylinder_d(d=self.guide_plate_bolt_diameter, h=100, center=True)
            )
            if not make_slot:
                nut_hole = rotate((0, 0, 90))(
                    self.tools.horizontal_cylinder_d(d=self.guide_plate_nut_diameter, h=100, center=False, segments=6)
                )
                result += nut_hole
            return result

        holes = None
        for y in y_offsets:
            for z in z_offsets:
                if make_slot:
                    new_hole = translate((0, y, z))(
                        hull()(
                            translate((0, slot_offset[0], 0))(hole()),
                            translate((0, slot_offset[1], 0))(hole())
                        )
                    )

                else:
                    new_hole = translate((0, y, z))(hole())
                if holes:
                    holes += new_hole
                else:
                    holes = new_hole
        return holes

    #########################################################################################
    # Utilities, procedures below this are not parts

    def get_blade_protector_origin(self):
        # Frame of reference for the protector.  I am choosing the right side of the protector
        origin_x = self.center_x - self.small_radius + self.c_form_brace_extension
        origin_y = -self.c_form_width / 2 - self.blade_protector_depth
        origin_z = self.center_z

        return origin_x, origin_y, origin_z

    def big_circle_parametric(self, radius, thickness=43):
        segments = 50
        if self.production:
            segments = 400
        obj = translate((self.center_x, self.center_y, self.center_z))(
            rotate((-90, 0, 0))(cylinder(r=radius, h=thickness, segments=segments)))
        return obj

    def big_circle(self):
        obj = self.big_circle_parametric(self.big_radius, thickness=self.c_form_width)
        return obj

    # The bolt will have a recessed head and will come up from below the base into a slotted
    # holder for the nut.
    def bottom_bolt(self):
        bolt_diameter = self.tools.bolt_sizes["1/4"]["bolt"]
        nut_diameter = 10.5
        bolt_hole = cylinder(d=bolt_diameter, h=1000)
        bolt_hole += cylinder(d1=bolt_diameter * 3, d2=bolt_diameter, h=bolt_diameter)

        return bolt_hole

    def base_connector_bolt_holes(self):
        # calculate the position of the bolt holes.
        x_delta = self.sub_base_bottom_section_thin_length / (self.number_of_base_bolts + 1)
        hole_offsets = [x_delta * (i + 1) for i in range(self.number_of_base_bolts)]

        # make the bolt holes.
        holes = None
        for x_index in range(self.number_of_base_bolts):
            x = hole_offsets[x_index]
            z_shift = 20
            if x_index > 2:
                z_shift = self.sub_base_bottom_section_thin_height - self.tools.bolt_sizes["1/4"]["depth"]

            # Acomodate for a 3 inch machine bolt.
            bolt = self.tools.hexagonal_bolt_hole_z(size="1/4", length=500)
            bolt = scale((1, 1, -1))(bolt)
            bolt = translate((x, 0, z_shift))(bolt)

            bolt += translate((x, 0, -self.base_thickness))(self.bottom_bolt())
            if not holes:
                holes = bolt
            else:
                holes += bolt

        return holes

    def horizontal_bolt_hole(self, sunken):
        bolt_hole = self.tools.horizontal_cylinder_d(d=6.5, h=400, center=True)
        if sunken:
            bolt_hole += self.tools.horizontal_cylinder_d1d2(d1=13, d2=6.5, h=6.5)
        return bolt_hole

    def side_sub_base_connector_bolt_holes(self):
        front_plate_offset = - self.c_form_width / 2 - self.plate_width
        sub_base_offset = - self.c_form_width / 2

        sunken_hole_positions = [
            (30, front_plate_offset, 30), (70, front_plate_offset, 30), (120, sub_base_offset, 30),
            (170, sub_base_offset, 30),
            (30, front_plate_offset, 60), (70, front_plate_offset, 60), (120, sub_base_offset, 60),
            (30, front_plate_offset, 90), (210, sub_base_offset, 12), (260, sub_base_offset, 12),
            (320, sub_base_offset, 12)
        ]
        flat_hole_positions = [
            (43, front_plate_offset, 190),
            (33, front_plate_offset, 220),
        ]

        bolt_holes = None
        for hole_position in sunken_hole_positions:
            bolt_hole = translate(hole_position)(self.tools.hexagonal_bolt_hole_y(size="1/4", length=1000))
            if bolt_holes:
                bolt_holes += bolt_hole
            else:
                bolt_holes = bolt_hole

        # two holes to compress the plates to hold the c_form
        for hole_position in flat_hole_positions:
            bolt_hole = translate(hole_position)(self.tools.hexagonal_bolt_hole_y(size="1/4", length=100))
            bolt_holes += bolt_hole

        return bolt_holes

    def hexagonal_grinder_holder(self):
        name = "hexagonal_grinder_holder"

        obj = self.wheel(False)
        cutter = translate((0, 0, -120))(cube((200, 200, 200), center=True))
        for i in range(6):
            obj = rotate((0, 60, 0))(obj)
            obj = obj - cutter

        return obj, name

    def square_grinder_holder(self):
        name = "square_grinder_holder"

        obj = self.wheel(False)
        cutter = translate((0, 0, -120))(cube((200, 200, 200), center=True))
        for i in range(4):
            obj = rotate((0, 90, 0))(obj)
            obj = obj - cutter

        return obj, name

    def test_c_form_groove(self):
        name = "test_c_form_groove"
        obj = self.c_form_groove(70, -90)
        obj = translate((-30, 0, -200))(obj)
        return obj, name


b = BandSaw()

b.render_all()
