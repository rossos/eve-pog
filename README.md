# eve-pog

The EVE Python Overview Generator is my adaptation of prior work by Leon Razor:
 * https://io.evansosenko.com/eve-overview/
 * https://github.com/razor-x/eve-overview/

The basic idea of Razor's work is to implement the Don't Repeat Yourself (DRY) principle in managing EVE overviews by allowing a user to create custom YAML files with human-readable names that define re-usable subsets of overview elements like groups and states. By combining these files, Razor's eve-overview Ruby script can compile an overview YAML file suitable for importing into the EVE client: groups and states files are aggregated to define presets, presets are used to define sets of tabs, and tabs together with other configuration files (appearance, columns, labels, and settings) define overview files. Updating an overview with a future element from CCP could be as simple as adding the new group ID into a single file, then re-compiling the overview to allow the reference to propagate into the final YAML file.

As I'm not very comfortable with Ruby as a language, I have re-written the core functionality of the script in Python as the Python Overview Generator. In the process, I have expanded on and tweaked some of its functionality. Part of this was to enable transferring the existing set of Z-S Overview files into the modular and re-usable format used by the eve-overview Ruby script and eve-POG:
  * https://github.com/Arziel1992/Z-S-Overview-Pack/

# PHO

From this conversion comes the Pandemic Horde Overview (PHO), starting from the latest ZS offering and adding in missing elements, including:
 * analysis beacons, cyno beacons, and mobile observatories
 * Lancer dreads
 * various NPCs (Homefront, Hidden Zenith, FW, Tutorial, etc.)

As this is an overview specifically for Pandemic Horde, other changes specifically useful for the alliance include:
 * prioritizing Excellent/Good standing over alliance (Pandemic Horde Inc. may show as light-blue to ESI corps, with proper standings set)
 * prioritizing Terrible/Bad standing over fleet and alliance (so awox or other enemies set red will be more immediately visible, as per Corp Bulletin)
 * de-emphasizing Allies in wars (so highsec-only allies will not appear blue in nullsec when they should be neut, as per Corp Bulletin)

# PHO vs ZS

A record of other notable changes from ZS to PHO follows below. I write this as an acknowledgement that significant changes should be made both carefully and openly, given how well-researched and widely-used ZS was as an overview package, and that any of these changes may need to be tweaked or reversed.

 * Removed most NPCs from Travel All, restricted now only to travel-specific threats and objects
 * Included all potentially-hostile NPCs to Brackets Travel
