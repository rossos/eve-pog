# How do I use this?

If you just want a workable overview for EVE Online, use the in-game channel `PH Overview` and follow the instructions there. Alternatively, you can download the YAML files from the `Overview` directory and import them manually in the game client using Overview Settings > Misc > Import Settings.

If you want to understand how eve-pog works or how PHO is generated, read on.


# What is an Overview?

From the point of view of the game client, the overview window in EVE displays objects to the player that can potentially be interacted with. This overview window has several tabs, each of which is essentially just a container for a pair of "filters" (formerly "presets"): one for the overview window itself, one for the brackets in space. These filters primarily determine which objects are displayed to the player and which are hidden. EVE's overview comes with default filters of minimal utility, while many player-designed overview packs exist that provide more useful sets of filters (like SaraShawa, Kismeteers, Z-S, and Iridium). Beyond filters, overview packs may also modify the appearance and precedence for displaying pilots based on states like standings and war status, the appearance and order of overview columns, and the label format for brackets.

From the point of view of someone trying to create custom overview settings, an overview is a [.YAML file](https://en.wikipedia.org/wiki/YAML) that specifies all of the above in a format that the game client can properly parse. Specifying **filters** (formerly **presets**) is the largest component of any custom overview, and deserves special attention.

Overview filters have three fields: the name of the filter, a list of EVE group IDs indicating which items will be displayed by this preset, and a list of states that the preset will always show/hide. The name is any valid string and is self-explanatory. The list of states is a list from a fixed set of integers representing states like "is in fleet", "is an empty wreck", or "has Bad standing". The list of group IDs is different because it will grow and change through game patches making it a problem for maintaining an overview. In particular, whenever new entities are added to the game (like new ship classes or new NPCs) they will often belong to entirely new groups with new ID numbers. Placing each of the new group IDs in the appropriate filters can become a headache.


# What is eve-pog?

The EVE Python Overview Generator is my adaptation of prior work by Leon Razor:
 * https://io.evansosenko.com/eve-overview/
 * https://github.com/razor-x/eve-overview/

The basic idea of Razor's work is to implement the Don't Repeat Yourself (DRY) principle in managing EVE overviews by allowing a user to create custom YAML files with human-readable names that define re-usable subsets of overview elements like groups and states. By combining these files, Razor's eve-overview Ruby script can compile an overview YAML file suitable for importing into the EVE client: groups and states files are aggregated to define "presets" (now filters), "presets" are used to define sets of tabs, and tabs together with other configuration files (appearance, columns, labels, and settings) define overview files. Updating an overview with a future element from CCP could be as simple as adding the new group ID into a single file, then re-compiling the overview to allow the reference to propagate into the final YAML file.

As I'm not very comfortable with Ruby as a language, I have re-written the core functionality of the script in Python as the Python Overview Generator (POG). In the process, I have expanded on and tweaked some of its functionality. Part of this was to enable transferring the existing set of Z-S Overview files into the modular and re-usable format used by the eve-overview Ruby script and eve-pog:
  * https://github.com/Arziel1992/Z-S-Overview-Pack/

This ended up being a partly manual (and therefore tedious) process. Starting with a conversion from Z-S into a format usable with eve-pog, then performing small modifications to include updates for newer entities and larger modifications to the handling of layout packs, the result is PHO (the Pandemic Horde Overview).

### Why EOOG?

The Eve Online Overview Generator uses modular design to facilitate easier maintenance of any overview pack. Based on the DRY principle, the overall approach is to allow re-using smaller components for each of the overview settings: appearance, columns, labels, and "presets". Each of these are defined as separate YAML files, which are compiled together by EOOG into a single overview file ready to be imported into the game client.

Preset files additionally rely on separate files defined for groups and states. Groups files are YAML files that have a single field "types" that give a list containing any mix of group IDs and "include" that gives names of other groups files. In this way, groups files may reference one another other allowing for custom levels of granularity. During compilation, all the group filenames are parsed in a preset file and the union of all their group IDs is taken to belong to that preset.

### Why Z-S?

Similarly, a nice feature of Z-S is the **modular** deployment of its overview settings. Users can load overview "packs" (these are technically several different overviews from the POV of the game client, just designed to play nicely together) by clicking individual in-game links, and each of these contains a bundle of presets. This takes advantage of the fact that the game client imports tab layouts by over-writing the previous tab layout while allowing filters to be loaded cumulatively (i.e., filters given by one overview will still be available even after loading a second overview). Z-S also gives a nice visualization for loading multiple overviews by intentionally mangling the tab display so that users know they are still at an intermediate step of the installation process.


### Why PHO?

From the conversion outlined above comes the Pandemic Horde Overview (PHO), starting from the latest Z-S offering and adding in missing elements, including:
 * analysis beacons, cyno beacons, and mobile observatories
 * Lancer dreads
 * various NPCs (Homefront, Hidden Zenith, FW, Tutorial, etc.)

As this is an overview specifically for Pandemic Horde, other changes specifically useful for the alliance include:
 * prioritizing Excellent/Good standing over alliance (Pandemic Horde Inc. may show as light-blue to ESI corps, with proper standings set)
 * prioritizing Terrible/Bad standing over fleet and alliance (so awox or other enemies set red will be more immediately visible, as per Corp Bulletin)
 * de-emphasizing Allies in wars (so highsec-only allies will not appear blue in nullsec when they should be neut, as per Corp Bulletin)


# Understanding eve-pog's workflow
The main entrypoint for eve-pog is the function `compile_overviews()` which aims to create an EVE client compatible YAML file based on overview description files. Each overview description file contains: references to files for the overview's appearance, columns, labels, and settings (for now, these are all 'default' files), followed by a list of "tabs" files, then a dictionary of presets files keyed by the names of the tabs files. The end result will be a separate EVE client compatible YAML file generated for each "tabs" entry.

## Overview Description Files
These are the .YML files located in the `overviews` directory that use YAML key/value pairs to specify modular components used in compiling the EVE client compatible overview file. Valid top-level keys for overview description files are: `appearance`, `columns`, `labels`, `settings`, `tabs`, and `presets`. Each key corresponds to settings that are expected by the EVE client when specifying overview behavior:

#### Appearance
  - Controls the general appearance settings and colortag/background color info. Should roughly correspond to the "Appearance" tab in the Overview Settings window in the EVE client.

#### Columns
  - Controls the visible columns and their ordering within each tab of the overview window. Should roughly correspond to the right-click "Columns" menu for each tab in the overview window in the EVE client.

#### Labels
  - Controls the bracket labels used by the EVE client in space with mouse-over. Should roughly correspond to the "Ships" tab in the Overview Settings window in the EVE client.

#### Settings
  - Additional user settings.

#### Tabs
  - Controls the number and name of tabs visible in the overview window and assigns initial filters (formerly "presets") to be active in each. Should roughly correspond to the "Tabs" tab in the Overview Settings window in the EVE client.

#### Presets
  - Controls the filters (formerly "presets") that will be included and made available by loading the resulting overview file. Should roughly correspond to contents of the "Filters" tab in the Overview Settings window in the EVE client.

Values for these keys are named references to other YAML files found under appropriately named directories, with file names using the .YML extension. As an example, a collection of settings named "default" used for the "appearance" key would be located at `appearances/default.YML`.

Note that both of the top-level keys `presets` and `tabs` are somewhat special in how they influence the ultimate output of an overview.

* The `tabs` key should contain a list of named tabs settings files (that is, names of .YML files located under the `tabs` directory). Each entry is interpreted as indicating that a separate overview output file should be generated using the given name. In the simplest case, a list with one entry will result in a single overview file being generated that can be imported into and used by the EVE client. As an example, if the `tabs` entry in our overview description file looks like this:
  ```
  tabs:
  - main
  - secondary
  ```
  then the eventual output of running eve-pog will be two EVE client compatible overview files that end in `_main.yaml` and `_secondary.yaml`, both located in the `Overview` (capital "O") directory.
 
* The `presets` key should contain a list of sub-keys with entries matching the list of named `tabs` settings already given. (Note that this is definitely redundant and should be patched in a future revision). Each of those sub-keys should have values that are a list of all the named "preset" files that are to be used with the associated tabs files. For example, the `presets` entry for our example above might look like this:
  ```
  presets:
    main:
    - travel_all
    - hostiles_all
    secondary:
    - dscan_all
    - pvx_all
  ```
  This indicates that exactly two filters ("presets") should be expected within each of the tabs files `main` and `secondary`.

## Tabs Files
The entries in our example above are referencing named YAML files contained in the `presets` and `tabs` directories. Tabs files contain a list where each entry contains the same four keys (`name`, `color`, `overview`, `bracket`) with values specifying the name of the tab, the color of the tab's name, the filter ("preset") used for the overview window with this tab, and the filter ("preset") used for the brackets with this tab. For example, `tabs/main.yml` might look like this:
```
- name: 'Travel'
  color: ''
  overview: travel_all
  bracket: travel_all
- name: 'Baddies'
  color: ''
  overview: hostiles_all
  bracket: travel_all
```

This is specifying an EVE overview that contains two tabs, the first of which uses a filter called `travel_all` for both its overview and brackets. The second uses `hostiles_all` for its overview and sticks with `travel_all` for its brackets. Note that the only filters mentioned in `tabs/main.yml` are the ones given in the list of filters in our sample overview description file above: `travel_all` and `hostiles_all`. 


## Filters and Presets Files
To understand the layout of presets files, we should first understand what these files are being used for. The EVE client expects filters in the form of a YAML entry mostly made up of a list of group IDs. An excerpt might look a bit like this:
```
groups:
  - 27
  - 381
  - 541
  - 833
  - 894
  - 898
  - 900
  - 906
```

This filter will display all hictors, dictors, recon ships, and battleships. (NB: the groups files use the misnomer "types" as a YAML key instead of "groups" and this should be patched in a future release) But without an encyclopedic knowledge of EVE group IDs  - or a willingness to exhaustively parse through online resources like [EVE Ref](https://everef.net/categories/) - it quickly becomes tedious and error-prone to manually manage such lists, especially when many of the same group ID entries will be re-used across many filters. This leads to the final building block for eve-pog: groups files.

### Groups Files: The Building Blocks of Presets
Groups are named YAML files containing a list of group IDs and/or a list of *other* named groups files that eve-pog can compile together into a single list that will be used for a filter. The name of a groups file should be human-readable and representative of the group IDs it contains. Each named filter, like "travel_all" in our running example above, is formed by eve-pog collecting named references of groups files that eventually resolve to lists of group IDs, then removing any duplicates, and finally producing a YAML list that contains all the resolved group ID entries. Instead of using the list of group IDs above, an eve-pog groups file might instead look like this:
```
include:
  - ship_dictors
  - ship_hictors
  - ship_recons
  - ship_battleship
```
This would direct eve-pog to look for files named `ship_dictors.yml`, `ship_hictors.yml`, etc., under the `groups` directory and attempt to compile them into a single list. This named filter can then be referenced from a tabs/presets file and the full list of group IDs will be used to generate the corresponding overview file for use in the EVE client.

This is substantially easier to manage. Filters now look like a list of human-readable and meaningful terms (like battleships, hictors, etc.). In addition, groups that are included in multiple filters can be updated by only modifying a single file; if dictors should be visible in both of our `travel_all` and `hostiles_all` filters and a new dictor group ID is added to the game, then this only involves modifying `ships_dictors.yml` and then re-compiling the overview.


## A Little Bit of Magic

On its own, this would be sufficient to generate an overview using modular groups files and keep the overview updated as fast as CCP can push out new group IDs. But eve-pog can also be used to generate overviews that replicate some of the clever ideas used by the popular Z-S overview.

### Filter Packs

One of the nicer ideas from Z-S is putting together an overview that accommodates filter "packs". For an in-game user, packs appear to be modular sets of filters that may be optionally loaded during an "installation" process for the Z-S overview. An initialization pack starts the installation and displays a message in the EVE client's overview; subsequent filter packs are added at the discretion of the user; and finally a layout is chosen to finalize the installation.

What is really happening here is that the Z-S overview is applying multiple overviews on top of each other. The EVE client appears to discard filters from previous overviews *only* if they were not directly loaded in a tab; filters that were loaded when a new overview was applied will still be available as an option in the new overview. So Z-S packs as many distinct filters as will fit into the overview and bracket filters, creates an overview out of that, and presents it to the user as a "filter pack". The purpose of the starting pack is largely to mangle the tab display and show the user a message (see the next section), the purpose of the finalizing pack is largely to fix up the tab names and layout that were previously mangled, and the purpose of the filter packs are to increase the number of filters available for the user to choose from.

### Mangled Tab Names

The final trick is to give the user enough information to know what to do. After applying the starter overview, all the tab names are set to be empty strings except for the first tab. The name of the first tab uses HTML and multiple lines to create a large displayed message in the overview window (telling them to apply another filter pack or apply a finalizing layout to finish the installation). All the intervening filter packs use the same tab naming trick to continue displaying the same message. Only the final "layout" pack will set the tab names to non-empty strings and restore the appearance of the EVE client's overview window.

### Fixing Tab Names

Since the EVE client will accept HTML formatting for tab names when specified by a YAML file but does not enable this in-game, applying a layout that uses "fancy" formatting can cause problems. In particular, if a user loads an overview that uses fancy formatting for the tab names then later tries to edit the overview settings through the EVE client, the color codes and other formatting will break. A work-around is to only use simple color formatting on tab names if we suspect the user may want to make in-game changes.



# Managing eve-pog groups files

Recall that groups files are YAML files identified by their filename (minus extension) that are used to reference collections of group IDs. These collections are used in filters to indicate which entries should and should not be displayed. For instance, if [group ID 27](https://everef.net/groups/27) is used in a preset but [group ID 26](https://everef.net/groups/26) is not, then (regular) Battleships will be visible when using the preset while (regular) Cruisers will not:
 
Groups files are structured to have up to two named entries: "types" is a list of group IDs and "include" is a list of names for other groups files. Groups files may have overlapping entries and may reference other groups files by name. The collection of group IDs for a named groups file is resolved by taking its own list of group IDs and iteratively amalgamating this (using a set union) with the collection of group IDs for each of the groups files named under its "include" entry. Thus, if one groups file includes another, this means it includes its collection of group IDs. Take care to avoid recursive references.

By convention, I treat groups filenames starting with an underscore "_" as root collections that contain only group IDs. These files are followed by [the name of the category](https://everef.net/categories) to which their entries belong, followed by another underscore, then a short (but descriptive and human-readable) name. I treat files without a leading underscore as composite collections that may reference other group files.

The process for detecting and adding new game entities to an overview follows:

1) Within the game client, open Overview Settings and Reset All Settings
2) From the Filters tab, under the Types Shown subtab click the Select All button. Then click the Save As button at the bottom of the window, and enter a name like "overview_all" and click OK.
3) From the Misc tab, click the button for Export Settings. In the window that appears, ensure that the box is checked next to "Tab Preset: overview_all" (or whatever equivalent name you chose in Step 2), enter "overview_all" in the File name field at bottom, and click Export.
4) You will be given the location of your saved YAML file (by default, under %user%/Documents/EVE/Overview). Copy this file to the same directory as the pog.py script.
5) Optional, but recommended: download the latest [invGroups](https://www.fuzzwork.co.uk/dump/latest/invGroups.csv) and [invCategories](https://www.fuzzwork.co.uk/dump/latest/invCategories.csv) CSV files from [Fuzzworks' SDE export](https://www.fuzzwork.co.uk/dump/latest/) and place them in the same directory as the pog.py script in order to automatically add annotations to the file generated in the next step.
6) Run the `determine_new_entities()` function within Python. This will expect the local file named "overview_all.yaml" (from Step 4) and will attempt to write any new entities to a YAML file "__new.yml" in the "groups" subdirectory.
7) Rename this file to match the file naming convention, or copy/paste the new entries individually into existing files, depending on how they could best be grouped together. If you create any new root groups files, also make sure to check whether any of the composite groups files should be including them.
8) Re-generate the overview files to incorporate the new group IDs.
