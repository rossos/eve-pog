import os
import csv
import re
from util import load_yaml_file, write_yaml_file, SQ

def load_invcategories():
    with open("invCategories.csv", "r") as file:
        cat_rows = list(csv.DictReader(file))
    return {int(row['categoryID']): row['categoryName'] for row in cat_rows}


def load_invgroups():
    cats = load_invcategories()

    with open("invGroups.csv", "r") as file:
        rows = list(csv.DictReader(file))
    return {int(row['groupID']): {
        'name': row['groupName'],
        'cat_name': cats[int(row['categoryID'])],
        'cat': int(row['categoryID'])
    } for row in rows}


def get_existing_presets_by_name():
    existing_presets = {}

    for filename in sorted(os.listdir("presets")):
        if os.path.isfile(os.path.join("presets", filename)) and filename[-4:] == ".yml":
            preset = load_yaml_file("presets", filename[:-4])
            existing_presets[preset['name']] = filename[:-4]

    return existing_presets


def write_annotated_states(filename, show, hide):
    all_states = {9: "Pilot has a security status below -5",
                  10: "Pilot has a security status below 0",
                  11: "Pilot is in your fleet",
                  12: "Pilot is in your Capsuleer corporation",
                  13: "Pilot is at war with your corporation/alliance",
                  14: "Pilot is in your alliance",
                  15: "Pilot has Excellent Standing.",
                  16: "Pilot has Good Standing.",
                  17: "Pilot has Neutral Standing.",
                  18: "Pilot has Bad Standing.",
                  19: "Pilot has Terrible Standing.",
                  21: "Pilot (agent) is interactable",
                  36: "Wreck is already viewed",
                  37: "Wreck is empty",
                  44: "Pilot is at war with your militia",
                  45: "Pilot is in your militia or allied to your militia",
                  48: "Pilot has No Standing.",
                  49: "Pilot is an ally in one or more of your wars",
                  50: "Pilot is a suspect",
                  51: "Pilot is a criminal",
                  52: "Pilot has a limited engagement with you",
                  53: "Pilot has a kill right on them that you can activate",
                  66: "Pilot is in your Non Capsuleer corporation"
                  }

    show, hide = sorted(show), sorted(hide)

    with open(filename, "w") as fileout:
        def write_state_line(s):
            try:
                fileout.write(f"  - {s:<10}# {all_states[s]}\n")
            except KeyError:
                print(f"No such state '{s}' - skipping writing to file")

        fileout.write("---\nshow: ")
        if len(show) < 1:
            fileout.write("[]\n")
        else:
            fileout.write("\n")
        for state in show:
            write_state_line(state)

        fileout.write("hide: ")
        if len(hide) < 1:
            fileout.write("[]\n")
        else:
            fileout.write("\n")
        for state in hide:
            write_state_line(state)
        fileout.write("\n")

    print(f"Wrote to file {filename}")


def parse_zs_preset(preset):
    show, hide = [], []

    name = preset[0]
    for subelt in preset[1]:
        tag = subelt[0]
        contents = subelt[1]
        if tag == "groups":
            groups = sorted(contents)
        elif tag == "alwaysShownStates":
            show = sorted(contents)
        elif tag == "filteredStates":
            hide = sorted(contents)

    return name, groups, show, hide


def convert_zs_presets(skip_existing=True):
    all_presets, existing_presets, existing_filenames = [], [], []
    preset_filename = None

    for filename in sorted(os.listdir("presets")):
        if os.path.isfile(os.path.join("presets", filename)) and filename[-4:] == ".yml":
            preset = load_yaml_file("presets", filename[:-4])
            existing_presets.append(preset['name'])
            existing_filenames.append(filename[:-4])

    for filename in sorted(os.listdir("zs")):
        if os.path.isfile(os.path.join("zs", filename)) and filename[-5:] == ".yaml":
            print(f"Opening file {filename}")
            zs_file = load_yaml_file("zs", filename[:-5])

            all_presets.extend(zs_file['presets'])

    for preset in all_presets:
        name, groups, show, hide = parse_zs_preset(preset)

        # Skip this conversion process if a preset file already exists bearing the same ZS preset name
        if name in existing_presets:
            if skip_existing:
                print(f"Skipping preset - file already exists for  {name}")
                continue
            else:
                preset_filename = existing_filenames[existing_presets.index(name)]

        groups, preset_show, preset_hide = set(groups), set(show), set(hide)
        #  State "20" is given by exported data from game, but does not match with any given entry in the UI!
        preset_show.difference_update(set([20]))
        preset_hide.difference_update(set([20]))
        group_names = []

        print(f"\n\tProcessing preset:   {name}")

        for file in sorted(os.listdir("groups")):
            if os.path.isfile(os.path.join("groups", file)) and file[-4:] == ".yml":
                #print(f"Loading group file {file}")
                filename = file[:-4]
                category_group = set(load_yaml_file("groups", filename)['types'])
                i = category_group.intersection(groups)
                if len(i) > 0:
                    #print("Found intersection")
                    groups.difference_update(i)
                    group_names.append(filename)
        if len(groups) > 0:
            i = input(f"Problem with groups, there are {len(groups)} elements remaining after removing all eligible "
                      f"category groups:\n {groups} \n (q)uit?")
            if i.lower() == "q":
                return 0

        states_name = None

        for file in sorted(os.listdir("states")):
            if os.path.isfile(os.path.join("states", file)) and file[-4:] == ".yml":
                filename = file[:-4]
                state = load_yaml_file("states", filename)
                state_show, state_hide = set(state['show']), set(state['hide'])

                if preset_show == state_show and preset_hide == state_hide:
                    print(f"State match in file '{filename}'")
                    states_name = filename
                    break

        filename = None
        for file in sorted(os.listdir("presets")):
            if os.path.isfile(os.path.join("presets", file)) and file[-4:] == ".yml":
                fn = file[:-4]
                preset = load_yaml_file("presets", fn)
                if preset['name'] == name:
                    filename = fn
                    print(f"Found existing preset file '{filename}'")
                    break

        if filename is None:
            filename = input("\nFilename for preset:  " + name + "\n") + ".yml"
        else:
            print(f"Over-writing existing preset file based on name match")
            filename = filename + ".yml"

        if states_name is None:
            states_name = filename
            print(f"\nUsing {states_name} as new filename for states file\n")
            write_annotated_states("states/" + states_name, preset_show, preset_hide)

        preset_dict = {
            "name": name,
            "symbol": "",
            "level": 0,
            "groups": group_names,
            "states": [states_name],
        }
        write_yaml_file(preset_dict, "presets/" + filename)

    print("Finishing.")


def merge_state_references(state_filename):
    states = load_yaml_file("states", state_filename)
    canonical_show, canonical_hide = set(states['show']), set(states['hide'])

    for file in sorted(os.listdir("presets")):
        if os.path.isfile(os.path.join("presets", file)) and file[-4:] == ".yml":
            filename = file[:-4]
            preset = load_yaml_file("presets", filename)
            state_name = preset['states'][0]

            referenced_states = load_yaml_file("states", state_name)
            referenced_show, referenced_hide = set(referenced_states['show']), set(referenced_states['hide'])

            if canonical_show == referenced_show and canonical_hide == referenced_hide:
                preset['states'] = state_filename
                write_yaml_file(preset, "presets/" + filename)
                print(f"Over-wrote {filename}: was '{state_name}', is now '{state_filename}'\n")
                return 0


def convert_zs_tabs():
    all_tabs, existing_presets, existing_filenames = [], [], []

    for filename in sorted(os.listdir("presets")):
        if os.path.isfile(os.path.join("presets", filename)) and filename[-4:] == ".yml":
            preset = load_yaml_file("presets", filename[:-4])
            existing_presets.append(preset['name'])
            existing_filenames.append(filename[:-4])

    existing_presets = get_existing_presets_by_name()

    for filename in sorted(os.listdir("zs")):
        if os.path.isfile(os.path.join("zs", filename)) and filename[-5:] == ".yaml":
            print(f"Opening file {filename}")
            filename = filename[:-5]
            zs_file = load_yaml_file("zs", filename)

            tabs_input = zs_file['tabSetup']
            tabs_output = []

            for tab in tabs_input:
                new_tab = {'name': None, 'color': None, 'overview': None, 'bracket': None}

                for k,v in tab[1]:
                    if k == "name" or k == "color":
                        nu_val = SQ(re.sub('Z-S', 'PHO', v)) if v is not None else ''  # Re-branding
                    elif k == "overview" or k == "bracket":
                        try:
                            nu_val = existing_presets[v]
                        except KeyError:
                            if v is None or v == "default" or v == "":
                                nu_val = "pvx_basic-plus-neut-plus-npc"  # POG cannot accept blank/null value here
                            else:
                                print(f" In {filename}, no preset file matching name '{v}' - skipping")
                                continue
                    else:
                        print(f" Found unknown key '{k}' in tabSetup - skipping")
                        continue

                    new_tab[k] = nu_val
                tabs_output.append(new_tab)

            write_yaml_file(tabs_output, "tabs/" + re.sub('zs', 'pho', filename) + ".yml")
            print("  Wrote to file " + "tabs/" + re.sub('zs', 'pho', filename) + ".yml")


def generate_zs_style_overview_files():
    existing_presets = get_existing_presets_by_name()

    output = {
        'appearance': 'default',
        'columns': 'default',
        'labels': 'default',
        'settings': 'default',
        'tabs': [],
        'presets': {},
    }

    for filename in sorted(os.listdir("zs")):
        if os.path.isfile(os.path.join("zs", filename)) and filename[-5:] == ".yaml":
            print(f"Opening file {filename}")
            filename = filename[:-5]
            zs_file = load_yaml_file("zs", filename)

            pho_filename = re.sub('zs', 'pho', filename)

            output['tabs'].append(pho_filename)
            output['presets'][pho_filename] = [existing_presets[p[0]] for p in zs_file['presets']]

    write_yaml_file(output, "overviews/pho.yml")


"""Attempts to convert an existing set of Z-S Overview files (contained in subdirectory "zs") into a set of files 
compatible with the format used by POG / EVE Online Overview Generator.
Not yet handled: appearance-related settings.
"""
if __name__ == "__main__":
    convert_zs_presets(skip_existing=False)
    convert_zs_tabs()
    generate_zs_style_overview_files()
