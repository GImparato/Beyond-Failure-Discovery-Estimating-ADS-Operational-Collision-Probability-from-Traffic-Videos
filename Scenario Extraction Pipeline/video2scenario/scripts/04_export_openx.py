import argparse, os, datetime
from utils.io_utils import read_json

OPENX_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<OpenSCENARIO xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="OpenSCENARIO.xsd">
  <FileHeader revMajor="1" revMinor="0" date="{{DATE}}" description="{{TITLE}}" author="video2scenario"/>
  <CatalogLocations/>
  <Parameters/>
  <RoadNetwork>
    <!-- TODO: collega alla tua mappa o road network di SVL -->
  </RoadNetwork>
  <Entities>
{{ENTITIES}}
  </Entities>
  <Storyboard>
    <Init>
      <Actions/>
    </Init>
    <Story name="MainStory">
      <Act name="Act1">
        <ManeuverGroup maximumExecutionCount="1" name="Group1">
{{MANEUVERS}}
        </ManeuverGroup>
        <StartTrigger>
          <ConditionGroup>
            <Condition name="Start" delay="0" conditionEdge="rising">
              <ByValueCondition>
                <SimulationTimeCondition value="0" rule="greaterThan"/>
              </ByValueCondition>
            </Condition>
          </ConditionGroup>
        </StartTrigger>
      </Act>
    </Story>
    <StopTrigger/>
  </Storyboard>
</OpenSCENARIO>
"""

ENTITY_TPL = """      <ScenarioObject name="agent_{id}">
        <Vehicle name="veh_{id}" vehicleCategory="{category}">
          <Performance maxSpeed="50" maxAcceleration="5.0" maxDeceleration="8.0"/>
          <BoundingBox dx="4.5" dy="1.8" dz="1.5" x="0" y="0" z="0"/>
          <Center x="0" y="0" z="0"/>
          <Axles>
            <FrontAxle maxSteering="0.5" wheelDiameter="0.6" trackWidth="1.6" positionX="3.1" positionZ="0.3"/>
            <RearAxle maxSteering="0.0" wheelDiameter="0.6" trackWidth="1.6" positionX="0.0" positionZ="0.3"/>
          </Axles>
        </Vehicle>
      </ScenarioObject>"""

MANEUVER_TPL = """          <Maneuver name="agent_{id}_man">
            <Event name="agent_{id}_ev" priority="overwrite">
              <Action name="agent_{id}_followtraj">
                <PrivateAction>
                  <RoutingAction>
                    <FollowTrajectoryAction>
                      <TrajectoryRef>
                        <Trajectory name="traj_{id}">
                          <Shape>
{poly_pts}
                          </Shape>
                          <Closed>false</Closed>
                        </Trajectory>
                      </TrajectoryRef>
                      <Timing domainAbsolute="false" offset="0" scale="1"/>
                    </FollowTrajectoryAction>
                  </RoutingAction>
                </PrivateAction>
              </Action>
              <StartTrigger>
                <ConditionGroup>
                  <Condition name="t0_{id}" delay="0" conditionEdge="rising">
                    <ByValueCondition>
                      <SimulationTimeCondition value="{t0}" rule="greaterThan"/>
                    </ByValueCondition>
                  </Condition>
                </ConditionGroup>
              </StartTrigger>
            </Event>
          </Maneuver>"""

POLY_PT_TPL = '                            <Polyline>\n{points}\n                            </Polyline>'
POINT_TPL = '                              <Vertex time="{t:.2f}">\n                                <Position>\n                                  <WorldPosition x="{x:.2f}" y="{y:.2f}" z="0" h="0"/>\n                                </Position>\n                              </Vertex>'

def map_class_to_category(cname):
    cname = (cname or "").lower()
    if cname in ["car","truck","bus","motorcycle","bicycle"]:
        return "car"
    if cname in ["person","pedestrian"]:
        return "pedestrian"
    return "car"

def build_entities(agents):
    parts = []
    for ag in agents:
        parts.append(ENTITY_TPL.format(id=ag["id"], category=map_class_to_category(ag.get("class","car"))))
    return "\n".join(parts)

def build_maneuvers(agents):
    mparts = []
    for ag in agents:
        traj = ag["trajectory"]
        pts = []
        for p in traj:
            pts.append(POINT_TPL.format(t=p["t"], x=p["x"], y=p["y"]))
        poly_block = POLY_PT_TPL.format(points="\n".join(pts))
        mparts.append(MANEUVER_TPL.format(id=ag["id"], poly_pts=poly_block, t0=max(0.0, ag.get("start_time",0.0))))
    return "\n".join(mparts)

def main():
    parser = argparse.ArgumentParser(description="Export OpenSCENARIO (template) da trajectories.json")
    parser.add_argument("--trajectories", required=True)
    parser.add_argument("--out", default="outputs/scenario.xosc")
    parser.add_argument("--title", default="video2scenario")
    args = parser.parse_args()

    data = read_json(args.trajectories)
    agents = data.get("agents", [])
    entities = build_entities(agents)
    maneuvers = build_maneuvers(agents)

    out_xml = (
        OPENX_TEMPLATE
        .replace("{{DATE}}", datetime.datetime.utcnow().isoformat())
        .replace("{{TITLE}}", args.title)
        .replace("{{ENTITIES}}", entities)
        .replace("{{MANEUVERS}}", maneuvers)
    )

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out_xml)
    print(f"[OK] OpenSCENARIO salvato in {args.out} (agents: {len(agents)})")

if __name__ == "__main__":
    main()
