import os
import re
from util import load_yaml_file, write_yaml_file, SQ, load_invgroups
from ruamel.yaml import CommentedMap


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


def get_existing_presets_by_name():
    existing_presets = {}

    for filename in sorted(os.listdir("presets")):
        if os.path.isfile(os.path.join("presets", filename)) and filename[-4:] == ".yml":
            preset = load_yaml_file("presets", filename[:-4])
            existing_presets[preset['name']] = filename[:-4]

    return existing_presets


def write_states_file(filename, show, hide):
    show, hide = sorted(show), sorted(hide)

    with open(filename, "w", encoding="utf8") as fileout:
        fileout.write("---\nshow: ")
        if len(show) < 1:
            fileout.write("[]\n")
        else:
            fileout.write("\n")
        write_annotated_states(fileout, show)

        fileout.write("hide: ")
        if len(hide) < 1:
            fileout.write("[]\n")
        else:
            fileout.write("\n")
        write_annotated_states(fileout, hide)
        fileout.write("\n")

    print(f"Wrote to file {filename}")


def write_annotated_states(file_handle, states):
    def write_state_line(s):
        try:
            file_handle.write(f"  - {s:<10}# {all_states[s]}\n")
        except KeyError:
            print(f"No such state '{s}' - skipping writing to file")
    for state in states:
        write_state_line(state)


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


def convert_zs_style():
    for filename in sorted(os.listdir("zs")):
        if os.path.isfile(os.path.join("zs", filename)) and filename[-5:] == ".yaml":
            print(f"Opening file {filename}")
            filename = filename[:-5]
            zs_file = load_yaml_file("zs", filename)

            appearance = {}
            keys_by_name = {
                "appearances": [
                    "flagOrder",
                    "flagStates",
                    "backgroundOrder",
                    "backgroundStates",
                    "stateBlinks",
                    "stateColorsNameList",
                ],
                "columns": [
                    "columnOrder",
                    "overviewColumns",
                ],
                "labels": [
                    "shipLabelOrder",
                    "shipLabels",
                ],
                "settings": [
                    "userSettings",
                ],
            }

            for name,keys in keys_by_name.items():
                data = CommentedMap()
                for k in keys:
                    data[k] = zs_file[k]
                    if k == "flagOrder" or k == "flagStates" or k == "backgroundOrder" or k == "backgroundStates":
                        for idx,d in enumerate(data[k]):
                            try:
                                state_desc = all_states[int(str(d))]
                            except KeyError:
                                # Handle state 20
                                data[k].yaml_add_eol_comment("Unknown", idx, column=12)
                            else:
                                data[k].yaml_add_eol_comment(state_desc, idx, column=12)

                write_yaml_file(data, name + "/default.yml", write_preamble=False)

        break  # only process the first ZS file, under the assumption that all have identical 'appearance' traits


def convert_zs_tabs():
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


def generate_overview_file():
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


def check_zs_presets_against_groups(category_prefix="_"):
    """Loads all presets given in .YML files contained in 'zs' subdirectory and checks them against the set of all .YML
    files contained in 'groups' subdirectory. For each preset, generates a list of groups files that share at least
    one group ID with the preset. For each groups file a non-empty intersection, list the group IDs from the groups file
    that are contained in the preset, as well as those IDs that are missing from the preset. Writes the results to
    'preset_check.txt'.

    :param category_prefix: prefix used for limiting the groups files checked against, e.g. "_entity". Default "_"
    """
    invgroups = load_invgroups()

    entity_groups = {}
    for file in sorted(os.listdir("groups")):
        if os.path.isfile(os.path.join("groups", file)) and file[-4:] == ".yml":
            if category_prefix is None or file[:len(category_prefix)] == category_prefix:
                print(f"Loading group file {file}")
                filename = file[:-4]
                entity_groups[filename] = set(load_yaml_file("groups", filename)['types'])

    zs_presets = []
    for filename in sorted(os.listdir("zs")):
        if os.path.isfile(os.path.join("zs", filename)) and filename[-5:] == ".yaml":
            print(f"Opening file {filename}")
            zs_file = load_yaml_file("zs", filename[:-5])

            zs_presets.extend(zs_file['presets'])

    entity_files, missing = {}, {}
    for preset in zs_presets:
        preset_name, preset_groups, show, hide = parse_zs_preset(preset)
        preset_groups = set(preset_groups)

        entity_files[preset_name], missing[preset_name] = {}, {}

        for filename, groupset in entity_groups.items():
            i = groupset.intersection(preset_groups)
            if len(i) > 0:
                # entity_files[preset_name].append(filename)  # add on filename for matching entity groups
                entity_files[preset_name][filename] = i
                d = groupset.difference(i)
                # print(f"groupset size {len(groupset)}, found intersection size {len(i)}, difference size {(len(d))}")
                if len(d) > 0:
                    missing[preset_name][filename] = d  # add on groupIDs missing from preset, if any

    with open("preset_check.txt", "w", encoding="utf8") as fileout:
        for name, files in entity_files.items():
            fileout.write(name + "\n\n")
            for filename, intersection in files.items():
                fileout.write("  - " + filename + "\n")
            fileout.write("\n")

            for fn, missing_set in missing[name].items():
                intersection = entity_files[name][fn]
                fileout.write(
                    f"  --- Groups missing from {fn} - ({len(missing_set)} / {len(intersection) + len(missing_set)}): \n")
                for m in missing_set:
                    fileout.write(f"    {m}  {invgroups[m]['name']} \n")
                fileout.write(
                    f"  +++ Groups contained in {fn} -  ({len(intersection)} / {len(intersection) + len(missing_set)}): \n")
                for e in intersection:
                    fileout.write(f"    {e}  {invgroups[e]['name']} \n")
                fileout.write("\n")

            fileout.write("\n\n")


"""Attempts to convert an existing set of Z-S Overview files (contained in subdirectory "zs") into a set of files 
compatible with the format used by POG / EVE Online Overview Generator.
Not yet handled: appearance-related settings.
"""
if __name__ == "__main__":
    #convert_zs_presets(skip_existing=False)
    #convert_zs_tabs()
    convert_zs_style()
    #generate_overview_file()
    #check_zs_presets_against_groups("_entity")


