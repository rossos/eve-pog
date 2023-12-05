# How do I use this?

Use the in-game channel `PH Overview` and follow the instructions there. Alternatively, download the YAML files from the `Overview` directory and import them manually using Overview Settings > Misc > Import Settings.

### What is an Overview?

From the point of view of the game client, the overview window in EVE displays objects to the player that can potentially be interacted with. This window has several tabs, each of which is a container for a pair of "presets": one for the overview window, one for the brackets. These presets determine which objects are actually displayed to the player and how they appear. The overview comes with default presets of minimal utility, while many player-designed overview packs exist that give more intricate and useful presets (like SaraShawa, Kismeteers, Z-S, and Iridium). Beyond presets, overview packs may also modify the appearance and precedence for displaying pilots based on states like standings and war status, the appearance and order of overview columns, and the label format for brackets.

From the point of view of someone trying to create custom overview settings, an overview is a .YAML file that specifies all of the above in a format that the game client will properly parse. Specifying **presets** is the largest component of any custom overview, and deserves special attention.

Overview presets have three fields: the name of the preset, a list of EVE group IDs indicating which items will be displayed by this preset, and a list of states that the preset will always show/hide. While the name is any valid string, and the list of states is a fixed list of integers, the list of groups is dynamic and a problem for maintaining an overview. Whenever new entities are added to the game (like new ship classes or new NPCs) they will belong to entirely new groups with new ID numbers. Placing each of the new group IDs in all of the appropriate presets can become a headache.


# eve-pog

The EVE Python Overview Generator is my adaptation of prior work by Leon Razor:
 * https://io.evansosenko.com/eve-overview/
 * https://github.com/razor-x/eve-overview/

The basic idea of Razor's work is to implement the Don't Repeat Yourself (DRY) principle in managing EVE overviews by allowing a user to create custom YAML files with human-readable names that define re-usable subsets of overview elements like groups and states. By combining these files, Razor's eve-overview Ruby script can compile an overview YAML file suitable for importing into the EVE client: groups and states files are aggregated to define presets, presets are used to define sets of tabs, and tabs together with other configuration files (appearance, columns, labels, and settings) define overview files. Updating an overview with a future element from CCP could be as simple as adding the new group ID into a single file, then re-compiling the overview to allow the reference to propagate into the final YAML file.

As I'm not very comfortable with Ruby as a language, I have re-written the core functionality of the script in Python as the Python Overview Generator. In the process, I have expanded on and tweaked some of its functionality. Part of this was to enable transferring the existing set of Z-S Overview files into the modular and re-usable format used by the eve-overview Ruby script and eve-POG:
  * https://github.com/Arziel1992/Z-S-Overview-Pack/

This ended up being a partly manual (and therefore tedious) process. Having done the conversion along with small modifications to include updates for newer entities, and larger modifications to the handling of layout packs, the result is PHO (the Pandemic Horde Overview).

### Why EOOG?

The Eve Online Overview Generator uses modular design to facilitate easier maintenance of any overview pack. Based on the DRY principle, the overall approach is to allow re-using smaller components for each of the overview settings: appearance, columns, labels, and presets. Each of these are defined as separate YAML files, which are compiled together by EOOG into a single overview file ready to be imported into the game client.

Preset files additionally rely on separate files defined for groups and states. Groups files are YAML files that have a single field "types" that give a list containing any mix of group IDs and names of other groups files. In this way, groups files may reference one another other allowing for custom levels of granularity. During compilation, all the groups filenames are parsed in a preset file and the union of all their group IDs is taken to belong to that preset.

### Why Z-S?

Similarly, a nice feature of Z-S is the modular deployment of its overview settings. Users can load overview "packs" (these are technically several different overviews from the POV of the game client, just designed to play nicely together) by clicking individual in-game links, and each of these contains a bundle of presets. This takes advantage of the fact that the game client imports tab layouts by over-writing the previous tab layout while allowing presets to be loaded cumulatively (i.e., presets given by one overview will still be available even after loading a second overview). Z-S also gives a nice visualization for loading multiple overviews by intentionally mangling the tab display so that users know they are still at an intermediate step of the installation process.


# PHO

From this conversion comes the Pandemic Horde Overview (PHO), starting from the latest ZS offering and adding in missing elements, including:
 * analysis beacons, cyno beacons, and mobile observatories
 * Lancer dreads
 * various NPCs (Homefront, Hidden Zenith, FW, Tutorial, etc.)

As this is an overview specifically for Pandemic Horde, other changes specifically useful for the alliance include:
 * prioritizing Excellent/Good standing over alliance (Pandemic Horde Inc. may show as light-blue to ESI corps, with proper standings set)
 * prioritizing Terrible/Bad standing over fleet and alliance (so awox or other enemies set red will be more immediately visible, as per Corp Bulletin)
 * de-emphasizing Allies in wars (so highsec-only allies will not appear blue in nullsec when they should be neut, as per Corp Bulletin)


# Understanding eve-pog's workflow

The main function `compile_overviews()` aims to compile all overview description files in the 'overviews' directory into game-client-compatible (GCC) YAML files in the 'Overview' directory. An overview description file contains: references to files for the appearance, columns, labels, and settings (for now, these are all 'default' files), followed by a list of "tabs" files, then a dictionary of presets files keyed by the names of the tabs files. The end result will be a separate GCC YAML file generated for each "tabs" entry.

Tabs files are located in the 'tabs' directory and their name (minus extension) should match what is given in the overview description file. These describe the tab layout and appearance for the GCC overview file that will be generated and should reference preset files by name. Currently, the referenced presets *must* match with the preset names given within the overview description file - at some point in the future, these should simply be detected automatically, because DRY. Note that the game client will only load a preset if it is used in one of the tabs or brackets: this means that giving a preset name in the overview description file without including it in one of the overview/bracket fields in the tabs file will result in that preset *not* being loaded by the game client.

Each entry under tabs and its corresponding list of presets is parsed; if no list of presets is given, by default the tab will have access to *all* named presets. The function `compile_overview()` (singular) is called once for each tab entry and does most of the heavy lifting for compiling and generating GCC YAML files.


# Managing eve-pog group files

Group files are YAML files identified by their filename (minus extension) that are used to reference collections of group IDs. These collections are used in presets to indicate which types should and should not be displayed. For instance, if [group ID 27](https://everef.net/groups/27) is used in a preset but [group ID 26](https://everef.net/groups/26) is not, then (regular) Battleships will be visible when using the preset while (regular) Cruisers will not:
 
Group files are structured to have up to two named entries: "types" is a list of group IDs and "include" is a list of group file names. Group files may have overlapping entries and may reference other group files by name. The collection of group IDs for a named group file is resolved by taking its own list of group IDs and iteratively amalgamating this (using a set union) with the collection of group IDs for each of the group files named under its "include" entry. Thus, if one group file includes another, this means it includes its collection of group IDs. Take care to avoid recursive references.

By convention, group files starting with an underscore "_" are root collections that contain only group IDs. These files are followed by [the name of the category](https://everef.net/categories) to which their entries belong, followed by another underscore, then a short (but descriptive and human-readable) name. Files without a leading underscore are composite collections that may reference other group files.

The process for detecting and adding new game entities to an overview follows:

1) Within the game client, open Overview Settings and Reset All Settings
2) From the Filters tab, under the Types Shown subtab click the Select All button. Then click the Save As button at the bottom of the window, and put in a name like "overview_all" and click OK.
3) From the Misc tab, click the button for Export Settings. In the window that appears, ensure that the box is checked next to "Tab Preset: overview_all" (or whatever equivalent name you chose in Step 2), enter "overview_all" in the File name field at bottom, and click Export.
4) You will be given the location of your saved YAML file (by default, under %user%/Documents/EVE/Overview). Copy this file to the same directory as the pog.py script.
5) Optional, but recommended: download the latest [invGroups](https://www.fuzzwork.co.uk/dump/latest/invGroups.csv) and [invCategories](https://www.fuzzwork.co.uk/dump/latest/invCategories.csv) CSV files from [Fuzzworks' SDE export](https://www.fuzzwork.co.uk/dump/latest/) in order to automatically add annotations to the file generated in the next step.
6) Within Python, run the `determine_new_entities()` function contained in the pog.py script. This will expect the local file named "overview_all.yaml" (from Step 4) and will attempt to write any new entities to a YAML file "__new.yml" in the "groups" subdirectory.
7) Rename this file to match the file naming convention, or copy/paste the new entries individually into existing files, depending on how they could best be grouped together. Check whether any of the group files with composite collections should include any of the new group files thus created.
8) Re-generate the overview files to incorporate the new group IDs
