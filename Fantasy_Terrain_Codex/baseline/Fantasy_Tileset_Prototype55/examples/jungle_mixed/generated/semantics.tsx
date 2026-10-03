<?xml version='1.0' encoding='UTF-8'?>
<tileset version="1.10" tiledversion="1.11.2" name="Semantic IDs (hidden)" tilewidth="128" tileheight="128" tilecount="13" columns="0" objectalignment="topleft">
  <tile id="0" type="sand">
    <properties>
      <property name="material_code" type="int" value="0" />
      <property name="semantic_axis" type="string" value="terrain" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/sand.png" width="128" height="128" />
  </tile>
  <tile id="1" type="grass">
    <properties>
      <property name="material_code" type="int" value="1" />
      <property name="semantic_axis" type="string" value="terrain" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/grass.png" width="128" height="128" />
  </tile>
  <tile id="2" type="water">
    <properties>
      <property name="material_code" type="int" value="2" />
      <property name="semantic_axis" type="string" value="terrain" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/water.png" width="128" height="128" />
  </tile>
  <tile id="3" type="plains">
    <properties>
      <property name="material_code" type="int" value="3" />
      <property name="semantic_axis" type="string" value="terrain" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/plains.png" width="128" height="128" />
  </tile>
  <tile id="4" type="unknown">
    <properties>
      <property name="material_code" type="int" value="255" />
      <property name="semantic_axis" type="string" value="terrain" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/unknown.png" width="128" height="128" />
  </tile>
  <tile id="5" type="broadleaf_forest">
    <properties>
      <property name="material_code" type="int" value="-1" />
      <property name="semantic_axis" type="string" value="forest" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/broadleaf_forest.png" width="128" height="128" />
  </tile>
  <tile id="6" type="pine_forest">
    <properties>
      <property name="material_code" type="int" value="-2" />
      <property name="semantic_axis" type="string" value="forest" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/pine_forest.png" width="128" height="128" />
  </tile>
  <tile id="7" type="hill">
    <properties>
      <property name="material_code" type="int" value="-3" />
      <property name="semantic_axis" type="string" value="relief" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/hill.png" width="128" height="128" />
  </tile>
  <tile id="8" type="mountain">
    <properties>
      <property name="material_code" type="int" value="-4" />
      <property name="semantic_axis" type="string" value="relief" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/mountain.png" width="128" height="128" />
  </tile>
  <tile id="9" type="jungle">
    <properties>
      <property name="material_code" type="int" value="-5" />
      <property name="semantic_axis" type="string" value="forest" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/jungle.png" width="128" height="128" />
  </tile>
  <tile id="10" type="tundra">
    <properties>
      <property name="material_code" type="int" value="4" />
      <property name="semantic_axis" type="string" value="terrain" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/tundra.png" width="128" height="128" />
  </tile>
  <tile id="11" type="snow">
    <properties>
      <property name="material_code" type="int" value="5" />
      <property name="semantic_axis" type="string" value="terrain" />
      <property name="semantic_only" type="bool" value="true" />
    </properties>
    <image source="semantic_tiles/snow.png" width="128" height="128" />
  </tile>
  <tile id="12" type="ice">
    <properties>
      <property name="material_code" type="int" value="-6" />
      <property name="semantic_axis" type="string" value="ice" />
      <property name="semantic_only" type="bool" value="true" />
      <property name="independent_of_terrain" type="bool" value="true" />
      <property name="underlying_terrain_code" type="int" value="2" />
    </properties>
    <image source="semantic_tiles/ice.png" width="128" height="128" />
  </tile>
</tileset>