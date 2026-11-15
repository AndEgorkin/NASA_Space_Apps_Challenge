# The Mars mission

Exploring Valles Marineris

A survival and exploration adventure for ages 7–12, created for the NASA International Space Apps Challenge.

You are an astronaut at a research base in Valles Marineris on Mars. Your rover is out in the canyon, your provisions are limited, and you have **30 real-time minutes of oxygen**. From the control room, you guide the rover to research sites to collect virtual rock samples and investigate the geology of the canyon. Complete **eight scientific missions** before your supplies run out to trigger your rescue and return home.

## Getting started

From the project directory, install the dependencies and launch the game.

```bash
python -m pip install -r requirements.txt
python Main.py
```

Select **Play** to start in the central corridor. Walk left into the control room, approach the computer desk from the right, and press **E** to take control of the rover. Press **M** to find the base, the underground ice extraction site, and the eight numbered research locations.

## Exploring the canyon

The missions introduce ancient water, landslides, seasonal dark streaks, rock layers, fractures, and safe route planning. You can tackle the missions in any order. Near a marked objective, press **E** to carry out one step, such as collecting a sample or recording an observation. Use the map’s task list to track your progress.

The blue square on the map marks the base, and the green arrow shows the rover. If the rover travels beyond the map, a green mark at the edge indicates its direction. Opening the map stops you from driving while you plan your route. Weather, electrical systems, and survival timers keep running.

## Solar power and rover hazards

A **sol** is approximately 24 hours and 40 minutes on Mars. In the game, one sol lasts **10 real-time minutes**. During **daylight**, the sunlit part of a sol, solar panels power the rover. Stop for at least three seconds during daylight to recharge its battery. At night the rover relies on stored charge.

Use the mouse wheel to adjust drive power from **0% to 200%**. Watch the battery as conditions change. Cold nights can cause temporary energy leaks, overheating affects performance, and dust storms increase energy costs and reduce traction. During a solar flare, interference builds until the rover loses its signal. Click the systems switch in the lower-right corner to turn the rover off before that happens. Driving resumes when you switch the systems back on.

## Life at the base

| Room | How to reach it | What you can do |
|---|---|---|
| Control room | Take the left exit from the central corridor. | Use the computer to operate the rover and analyze returned samples when a task calls for it. |
| Crew quarters | Take the right exit, then head up the side corridor. | Approach the lower edge of a bed and press **E** at night to sleep until 09:00 local solar time. |
| Hydroponics room | Take the right exit, then head down the side corridor. | Approach the upper edge of the growing beds and press **E** to use water from your inventory. |

Sleeping skips the night. The skipped hours still use oxygen and provisions at the game’s compressed time scale, so check your reserves before going to bed. The rover must recharge using its solar panels.

### From ice to drinking water and provisions

1. Complete the two research steps in **Mission 5** to discover underground ice. Then press **E** at the same site to extract ice from beneath the Martian surface. The rover can carry up to five units of ice.
2. Drive the rover back to the outside of the base and press **E** to unload. The ice is melted at the base, making water available to the astronaut. Returning to the control room with **Esc** leaves the cargo on the rover.
3. Use the delivered water in the greenhouse. The base grows **dwarf red radishes** in hydroponic beds, where water carries nutrients to the roots. Their compact size suits the small growing area.
4. In the prototype, tending and harvesting the radishes take one interaction. One unit of water restores 30 percentage points of provisions, up to 100%. When provisions are full, the water stays in your inventory.

### Experimental power at the base

The base design draws inspiration from a 2018 drop-tower study in which researchers used light to produce hydrogen under brief conditions of microgravity. The game imagines a base that uses solar electricity during daylight to split water into hydrogen and oxygen. At night, a fuel cell recombines the stored gases to generate electricity and produce water. This hydrogen/fuel-cell system is a narrative concept, not an implemented resource-conversion mechanic. Oxygen stored for power generation stays in that imagined system. The astronaut has a separate, limited breathing supply. [Read the 2018 study in *Nature Communications*.](https://www.nature.com/articles/s41467-018-04844-y)

## Controls

| Input | Action |
|---|---|
| **WASD** or **arrow keys** | Walk around the base. In rover mode, **W/S** drive and **A/D** steer. While the manipulator is deployed, **WASD** moves its gripper instead. |
| **E** | Interact with the nearby computer, bed, growing bed, underground ice extraction site, unloading point, or mission objective. With the manipulator active, grab the sample or store it in the tray. |
| **M** | Open or close the rover map. |
| **Mouse wheel** | Adjust rover drive power. |
| **On/off switch** | Toggle rover systems. Switch off for protection during a solar flare. |
| **Esc** | Cancel the manipulator if active; otherwise close the map first. From rover control, return to the computer. At the base, open the menu. |
| **Up/Down** or **Tab**, then **Enter** or **Space** | Select and confirm a menu option. The menu also supports the mouse. |
| **Enter** on the result screen | Begin a new attempt with fresh supplies and mission progress. |

## Survival, rescue, and saves

The upper-right display tracks oxygen, provisions, and water. A full stock of provisions lasts **15 real-time minutes** without replenishment. Oxygen and provisions are consumed while you walk around the base, drive the rover, or read the rover map. The main menu pauses consumption. Select **Play** to resume.

Finishing all eight missions triggers evacuation. Running out of oxygen or provisions, draining the rover battery, or losing the signal to an unprotected solar flare ends the attempt.

Switching between the base and rover preserves their state during the current attempt. There are **no disk saves**: each new launch starts fresh with the rover near the base, full supplies, and no completed missions. Old save files are ignored. The sol clock and weather continue while the astronaut is at the base, even before the first rover session. **Load** and **Settings** remain placeholders.

## NASA data and resources

| Link text | Use in the project | Link URL |
|---|---|---|
| Mars surface map — NASA Mars Trek | Geographic reference for Valles Marineris and the rover map. The terrain is procedural and mission markers are placed for gameplay. | [https://trek.nasa.gov/](https://trek.nasa.gov/) |
| Mars sol length — NASA Mars Facts | Reference for the length of a sol, compressed into the game’s ten-minute cycle. | [https://science.nasa.gov/mars/facts/](https://science.nasa.gov/mars/facts/) |
| Mars surface temperature — NASA Planetary Spectrum Generator | Reference for Martian surface temperatures, simplified for the rover’s temperature and power mechanics. | [https://psg.gsfc.nasa.gov/apps/mars/](https://psg.gsfc.nasa.gov/apps/mars/) |

Evidence of ancient water helps scientists investigate what Mars was like long ago. It does not prove that liquid water flows there now. The seasonal dark streaks give players a chance to compare observations before drawing a conclusion. The underground ice extraction site is a fictional resource location created for the game.

## Development

Run the test suite from the project directory.

```bash
python -m unittest discover -s tests -v
```

Use `camelCase` for variables and functions, `PascalCase` for class names, and a leading underscore for private fields and methods, such as `_doSomething()`. Keep one class per file and put executable logic inside functions or methods.


## Research missions

Open the rover map with **M** to see eight numbered research sites and their progress. Drive close to a marker and press **E** once for each step shown in the interaction hint. Most missions use two interactions at the same site. Missions can be attempted in any order, subject to the requirements below. Research actions are simplified virtual measurements; marker positions are chosen for gameplay rather than precise geographic accuracy.

| # | Mission | Location | How to complete it |
|---|---|---|---|
| 1 | **The Ancient Water Mystery** | Hebes / Candor Chasma | Press **E** at the site to deploy the manipulator. Move the gripper to the sample with **WASD** and press **E** to grab it. Move to the left **TRAY** and press **E** to store the sample; only then is collection credited. **Esc** cancels without awarding the sample. Rover driving is disabled while the arm is active. After storage, press **E** to measure mineral composition. Return the rover to the outside of the base. Press **Esc**, approach the control-room computer, and press **E** to analyze the returned sample. This final analysis completes the mission; another **E** resumes rover control. |
| 2 | **The Great Landslide** | Ius Chasma | Press **E** to map the debris, then again to inspect exposed rock layers. The observations help reconstruct how the landslide changed the canyon. |
| 3 | **The Mysterious Dark Streaks** | Melas / Coprates Chasma | Press **E** to compare seasonal images, then again to take a remote measurement. The cause of these streaks remains debated: salts and dry flows are possible explanations, and liquid water is not confirmed. |
| 4 | **The Geological Archive** | Hebes Chasma | Press **E** to photograph the rock layers, then again to compare their sequence and reconstruct the relative order of geological events. |
| 5 | **The Lost Underground Reservoir** | Eastern Valles Marineris | Press **E** to map collapsed terrain, then again to scan and discover underground ice. Completing these steps unlocks ice extraction at the same site. Subsequent **E** presses collect ice into the rover, up to five units. Return to the outside of the base and press **E** to unload and melt it: one unit of ice becomes one unit of water in the base inventory. The accessible deposit is a fictional gameplay resource. |
| 6 | **The Planetary Fracture** | Noctis Labyrinthus | Press **E** to map fractures, then again to measure an elevation profile. These observations introduce tectonics and the influence of the Tharsis uplift. |
| 7 | **The Impossible Route** | Canyon-floor route | Drive the extended route through **five ordered waypoints**: enter the field, pass the first rock gate, navigate the middle section, clear the final gate, and finish. **Nine solid rocks** have collision boundaries and gaps wide enough to drive between them. Steer through the openings and press **E** at each waypoint. Marker **7** advances after each checkpoint; the map shows the complete route. Collisions check movement and rotation in small steps and allow sliding along rock faces. |
| 8 | **The Canyon Research Station** | Base plateau | First deliver at least one unit of ice and convert it to water at the base. Use water to tend the hydroponic beds at least once while provisions are below full. Then operate the rover near the outside of the base and press **E** to deploy the station. |

### Completion and rescue

The mission counter tracks **0/8** through **8/8**. Completing all eight missions while survival reserves remain triggers the rescue ending automatically. Oxygen lasts **30 real-time minutes** and cannot currently be replenished. Exhausted oxygen or provisions ends the attempt; a flat rover battery or signal loss during an unprotected solar flare also causes failure. Press **Enter** on the result screen to begin a new attempt. Mission progress is kept only for the current run.
