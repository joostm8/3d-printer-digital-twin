import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as BufferGeometryUtils from 'three/addons/utils/BufferGeometryUtils.js';
import GUI from 'lil-gui';

// 1. Create the scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xF2F2F2);
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight,
   0.1, 1000);

// Set camera position and rotation (obtained these by orbit controlling and logging the values to the console.)
camera.position.set(0.9785464731744354, 0.7830072385726516, 1.9722658421507302);
camera.rotation.set(-0.377925250059398, 0.4320800467455752, 0.1647449109930175);

// this was a good starting view.
// camera.position.set(1.5,2, 1.5);
// camera.lookAt(0, 0, 0);
const renderer = new THREE.WebGLRenderer({ antialias: true }); // smooth edges
renderer.setSize(window.innerWidth, window.innerHeight);
// if performance needed: setSize(window.innerWidth/2, window.innerHeight/2, false) renders at half resolution.
document.body.appendChild(renderer.domElement);

// Add lights

const hemilight = new THREE.HemisphereLight(0xffffff, 0x444444, 1);
hemilight.position.set(0, 10, 0);
scene.add(hemilight);

const dirlight = new THREE.DirectionalLight(0xffffff, 5);
dirlight.position.set(-75, 75, 75);
scene.add(dirlight);

// 2. Add controls
const controls = new OrbitControls( camera, renderer.domElement );
controls.enableDamping = true;

controls.update();

// 2. Add something to render, a cube
// const geometry = new THREE.BoxGeometry( 1, 1, 1 );
// const material = new THREE.MeshBasicMaterial( { color: 0x00ff00 } );
// const cube = new THREE.Mesh( geometry, material );
// scene.add( cube );


const loader = new GLTFLoader();

loader.load( './static/ender3v2.glb', function ( gltf ) {

  const model = gltf.scene;
  model.scale.set(3, 3, 3);       // Adjust model scale
  
  model.rotation.x = Math.PI/2; // Adjust model rotation.
  model.rotation.z = -Math.PI/2;
  model.position.set(-0.6, -0.9, 0);    // Adjust model position
  console.log(model)
  model.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      // console.log(child);
      if (child.material instanceof THREE.MeshStandardMaterial) {
        //console.log(child.geometry.attributes.normal.array);
        child.material.metalness = 0;
        // console.log(child.material);
      }
    }
  });
  scene.add( model );

  // --- lil-gui controls for axis sub-assemblies ---
  // Sub-assembly node names provided by the user:
  // Y: "SUB_ASSY_Base_Y Axis_Bed"
  // X: "Sub_Assy_Hotend-X Axis"
  // Z: "SUB_ASSY_X Axis_Complete"

  const partY = model.getObjectByName('SUB_ASSY_Base_Y_Axis_Bed');
  const partX = model.getObjectByName('Sub_Assy_Hotend-X_Axis');
  const partZ = model.getObjectByName('SUB_ASSY_X_Axis_Complete');

  const initialPos = {
    x: partX ? partX.position.clone() : new THREE.Vector3(),
    y: partY ? partY.position.clone() : new THREE.Vector3(),
    z: partZ ? partZ.position.clone() : new THREE.Vector3(),
  };
  const xzOffset = initialPos.x.z - initialPos.z.z;
  console.log(initialPos)

  const gui = new GUI();
  const folder = gui.addFolder('Axes');

  // Choose reasonable default ranges; adjust if the model uses different units/scale
  const range = 0.5; // +/- range in scene units

  // Axis limits and offsets
  const limits = {
    x: { min: 0.038, max: 0.294 },
    y: { min: -0.102, max: 0.134 },
    z: { min: -0.53, max: -0.283 }
  };

  if (partX) {
    const paramsX = { value: 0 };
    const absX = { value: partX.position.y };
    const rangeX = limits.x.max - limits.x.min;
    folder.add(paramsX, 'value', 0, rangeX, 0.001).name('X (Y axis)').onChange((v) => {
      partX.position.y = limits.x.min + v;
      absX.value = partX.position.y;
      console.log('X absolute position (Y axis):', partX.position.y);
      absXController.updateDisplay();
      // Extrusion update on manual move
      AddExtrusionPoint();
    });
    const absXController = folder.add(absX, 'value').name('X abs (Y axis)').listen();
    // Initialize position
    partX.position.y = limits.x.min;
    absX.value = partX.position.y;
  } else {
    console.warn('Part X not found: Sub_Assy_Hotend-X Axis');
  }

  if (partY) {
    const paramsY = { value: 0 };
    const absY = { value: partY.position.x };
    const rangeY = limits.y.max - limits.y.min;
    folder.add(paramsY, 'value', 0, rangeY, 0.001).name('Y (X axis)').onChange((v) => {
      partY.position.x = limits.y.max - v; // Invert: 0 = max, max = min
      absY.value = partY.position.x;
      console.log('Y absolute position (X axis):', partY.position.x);
      absYController.updateDisplay();
      // Extrusion update on manual move
      AddExtrusionPoint();
    });
    const absYController = folder.add(absY, 'value').name('Y abs (X axis)').listen();
    // Initialize position
    partY.position.x = limits.y.max;
    absY.value = partY.position.x;
  } else {
    console.warn('Part Y not found: SUB_ASSY_Base_Y Axis_Bed');
  }

  if (partZ) {
    const paramsZ = { value: 0 };
    const absZ = { value: partZ.position.z };
    const rangeZ = limits.z.max - limits.z.min;
    folder.add(paramsZ, 'value', 0, rangeZ, 0.001).name('Z (Z axis)').onChange((v) => {
      partZ.position.z = limits.z.max - v; // Invert: 0 = max, max = min
      if (partX) {
        partX.position.z = limits.z.max - v + xzOffset;
      }
      absZ.value = partZ.position.z;
      console.log('Z absolute position (Z axis):', partZ.position.z);
      absZController.updateDisplay();
      // Extrusion update on manual move
      AddExtrusionPoint();
    });
    const absZController = folder.add(absZ, 'value').name('Z abs (Z axis)').listen();
    // Initialize position
    partZ.position.z = limits.z.max;
    absZ.value = partZ.position.z;
    if (partX) partX.position.z = limits.z.max + xzOffset;
  } else {
    console.warn('Part Z not found: SUB_ASSY_X Axis_Complete');
  }




  // --- Extrusion path offset setup ---
  let extrusionOffset = null;
  const extrusionStart = new THREE.Vector3(-0.44400000035017734, -0.05059827744040137, -0.4023169025964177); // checked where the extrusion starts with raytrace clicking.
  const nozzlePos = new THREE.Vector3(-0.39826328364276475, -0.1627760342037571, -0.0404177947703212); // checked where the nozzle is at that point with raytrace clicking.
  extrusionOffset = new THREE.Vector3().subVectors(extrusionStart, nozzlePos);
  extrusionOffset.x = -0.0865; // bit of a manual offset to get things to align. Not sure why normal offsetting didn't work.
  extrusionOffset.z = 0.0412;
  console.log('Nozzle world position (extrusion offset):', extrusionOffset);

  // --- Unified extrusion path update ---
  function AddExtrusionPoint() {
    if (!printerState.extruding) return;
    if (partX && partY && partZ) {
      const xWorld = new THREE.Vector3();
      const yWorld = new THREE.Vector3();
      const zWorld = new THREE.Vector3();
      partX.getWorldPosition(xWorld);
      partY.getWorldPosition(yWorld);
      partZ.getWorldPosition(zWorld);
      // Use the correct mapping for your printer (X, Z, Y)
      const newPoint = new THREE.Vector3(xWorld.x, zWorld.y, -yWorld.z); // store the coordinates in the y-local frame (as if the printhead moved negatively and the platter stayed still)
      // then offset these points in the rendering with the current Y-carriage position (in world coordinates, this is done in updateExtrusionMesh function)
      // Subtract nozzle offset so extrusion starts at (0,0,0)
      const correctedPoint = new THREE.Vector3().subVectors(newPoint, extrusionOffset);      
      extrusionPath.push(correctedPoint);
      console.log('Extrusion path added (offset):', correctedPoint);
      updateExtrusionMesh();
    }
  }

  folder.open();

  // --- Extrusion state and GUI ---
  const printerState = {
    extruding: false,
    extrusionWidth: 0.0045,
    extrusionDepth: 0.003
  };
  let extrusionPath = [];
  let currentLayerZ = null;
  let extrusionMeshIntermediate = null; // mesh of the currently being extruded Z layer
  let mergedGeometry = null; // all previously finished layers get merged into this geometry
  let mergedMaterial = new THREE.MeshStandardMaterial({ color: 0x0077ff });
  let mergedMesh = null;

  // Add extrusion controls to GUI
  const extrusionFolder = gui.addFolder('Extrusion');
  extrusionFolder.add(printerState, 'extruding').name('Extruding').onChange((v) => {
    if (!v) extrusionPath.length = 0; // Reset path when turning off
    updateExtrusionMesh();
  });
  extrusionFolder.add(printerState, 'extrusionWidth', 0.001, 0.01, 0.0001).name('Width').onChange(updateExtrusionMesh);
  extrusionFolder.add(printerState, 'extrusionDepth', 0.001, 0.01, 0.0001).name('Depth').onChange(updateExtrusionMesh);
  extrusionFolder.open();

  // --- Extrusion mesh update ---
  function updateExtrusionMesh() {
    if (extrusionMeshIntermediate) { // updateExtrusionMesh is only called when it really needs to be deleted, so always do this.
      scene.remove(extrusionMeshIntermediate);
      extrusionMeshIntermediate.geometry.dispose();
      extrusionMeshIntermediate.material.dispose();
    }
    if (extrusionPath.length < 2) return;
    // Polyline extrusion: create a tube geometry along the path
    const w = printerState.extrusionWidth;
    const d = printerState.extrusionDepth;
    const material = new THREE.MeshStandardMaterial({ color: 0x0077ff });
    // Create a curve through the path
    const curve = new THREE.CatmullRomCurve3(extrusionPath);
    const tubularSegments = Math.max(10, extrusionPath.length * 4);
    const radius = Math.max(w, d) / 2;

    const geometry = new THREE.TubeGeometry(curve, tubularSegments, radius, 8, false);
    extrusionMeshIntermediate = new THREE.Mesh(geometry, material);
    scene.add(extrusionMeshIntermediate);
    // for rendering, all the y-axis points should be shifted with the current y-axis position.
    const yWorld = new THREE.Vector3(null);
    partY.getWorldPosition(yWorld);
    extrusionMeshIntermediate.translateZ(yWorld.z);
    // const zdiff = extrusionPath[extrusionPath.length-1].z;
    // extrusionMesh.translateZ(zdiff);
    // when we add a point to the mesh, when the y-axis moves, it shifts with it all the other existing points.
    //scene.add(extrusionMeshZ);

    // at this point, we should also update the position of the mergedMesh
    if(mergedMesh){
      // in contrast with the other mesh, here we don't need to translate, but update the Y (z) position directly.
      mergedMesh.position.setZ(yWorld.z);
      // console.log(yWorld.z);
      // console.log(mergedMesh.position);
    }
  }

  // --- WebSocket for updating axis positions and extrusion state ---
  function clamp(val, min, max) {
    if (val < min) {
      console.warn(`Value ${val} below min ${min}, clamping.`);
      return min;
    }
    if (val > max) {
      console.warn(`Value ${val} above max ${max}, clamping.`);
      return max;
    }
    return val;
  }

  function updateAxes({ x, y, z, e}) {
    console.log(x, y, z)
    // Treat x, y, z as slider values (0 to range)
    let posChanged = false;
    let absX, absY, absZ;
    if (partX) {
      const rangeX = limits.x.max - limits.x.min;
      const xClamped = clamp(x ?? 0, 0, rangeX);
      absX = limits.x.min + xClamped;
      if (partX.position.y !== absX) posChanged = true;
      partX.position.y = absX;
    }
    if (partY) {
      const rangeY = limits.y.max - limits.y.min;
      const yClamped = clamp(y ?? 0, 0, rangeY);
      absY = limits.y.max - yClamped; // Inverted
      if (partY.position.x !== absY) posChanged = true;
      partY.position.x = absY;
    }
    if (partZ) {
      const rangeZ = limits.z.max - limits.z.min;
      const zClamped = clamp(z ?? 0, 0, rangeZ);
      absZ = limits.z.max - zClamped; // Inverted
      if (partZ.position.z !== absZ) posChanged = true;
      partZ.position.z = absZ;
      if (partX) partX.position.z = absZ + xzOffset;
    }
    
    // If extruding and position changed, add to path and update mesh
    if (posChanged){
      console.log("pos changed, updating viz")
      if(extrusionPath.length > 1){
        finalizeCurrentMesh();
      }
      if(e){
        // if extruding, add extrusionpoint
        printerState.extruding = true;
        AddExtrusionPoint();
      }else{
        // if not extruding, finalize current mesh (if any)
        finalizeCurrentMesh();
        printerState.extruding = false;
      }
    }else{
      console.log("pos not changed.")
    }
  }

  function finalizeCurrentMesh() {
    if (!extrusionMeshIntermediate) return;

    // Merge current layer into mergedGeometry
    const geom = extrusionMeshIntermediate.geometry;
    if(!mergedGeometry){
      // if unexistant, create a new geometry based on the old one.
      mergedGeometry = geom;
      mergedMesh = new THREE.Mesh(mergedGeometry, mergedMaterial);
      scene.add(mergedMesh);
    }else{
      mergedGeometry = BufferGeometryUtils.mergeGeometries([mergedGeometry, geom]);
    }
    
    // Replace mergedMesh geometry
    mergedMesh.geometry.dispose();
    mergedMesh.geometry = mergedGeometry;

    // Cleanup current mesh
    scene.remove(extrusionMeshIntermediate);
    extrusionMeshIntermediate.geometry.dispose();
    extrusionMeshIntermediate.material.dispose();
    extrusionMeshIntermediate = null;
    
    // Keep the last entry, otherwise we'll end up with holes in the mesh.
    extrusionPath = [extrusionPath[extrusionPath.length-1]];
  }

  function updateExtrusion({ extruding, extrusionWidth, extrusionDepth }) {
  if (typeof extruding === 'boolean') printerState.extruding = extruding;
  if (typeof extrusionWidth === 'number') printerState.extrusionWidth = extrusionWidth;
  if (typeof extrusionDepth === 'number') printerState.extrusionDepth = extrusionDepth;
  }

  // function to reset the current mesh.
  function resetMesh(){
    console.log("new print started, disposing of old meshes")
    // first dispose, then set to null.
    if(mergedMesh){
      scene.remove(mergedMesh)
      mergedMesh.geometry.dispose()
      mergedMesh.material.dispose()
    }
    if(extrusionMeshIntermediate){
      scene.remove(extrusionMeshIntermediate)
      extrusionMeshIntermediate.geometry.dispose()
      extrusionMeshIntermediate.material.dispose()
    }
      extrusionPath = [];
      extrusionMeshIntermediate = null; // mesh of the currently being extruded Z layer
      mergedGeometry = null; // all previously finished layers get merged into this geometry
      mergedMesh = null;
  }

let ws;
const RETRY_DELAY = 500; // 500 ms

function setupWebSocket(url) {
  ws = new WebSocket(url);
  ws.onopen = () => {console.log('WebSocket connected');};
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case 'positionUpdate':
          updateAxes(data);
          break;
        case 'extrusion':
          updateExtrusion(data);
          break;
        case 'mesh':
          if(data.reset){
            resetMesh()
          }
          break;
        default:
          console.warn('Unknown packet type:', data.type);
      }
    } catch (e) {
      console.error('WebSocket message error:', e);
    }
  };
  ws.onclose = () => {
    console.log('WebSocket closed, retrying in', RETRY_DELAY, 'ms');
    setTimeout(() => setupWebSocket(url), RETRY_DELAY);
  };
  ws.onerror = (err) => {
    console.error('WebSocket error:', err, 'Retrying in', RETRY_DELAY, 'ms');
    ws.close(); // ensure onclose is triggered
  };
}

setupWebSocket('ws://localhost:9090');

  // --- Nozzle search helper: log all objects containing 'nozzle' (case-insensitive) ---
  // model.traverse((child) => {
  //   if (child.name && child.name.toLowerCase().includes('nozzle')) {
  //     console.log('Possible nozzle candidate:', child.name);
  //   }
  // });

  

}, undefined, function ( error ) {

  console.error( error );

} );

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function onClick(event) {
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(scene.children, true);

  if (intersects.length > 0) {
    const point = intersects[0].point; // world coordinates
    console.log(point);
  }
}

window.addEventListener('click', onClick);


// 3. Animation loop
function animate() {
  controls.update();
  renderer.render( scene, camera );
}
renderer.setAnimationLoop( animate );

// 4. Websocket for updating axis positions in real-time.

// Axis update handler
// function updateAxes({ x, y, z }) {
//   if (partX) partX.position.y = (x ?? 0); // X subassembly along Y
//   if (partY) partY.position.x = (y ?? 0); // Y subassembly along X
//   if (partZ) {
//     partZ.position.z = (z ?? 0);
//     if (partX) partX.position.z = (z ?? 0); // X subassembly with Z
//   }
// }

// let ws;
// function setupWebSocket(url) {
//   ws = new WebSocket(url);
//   ws.onopen = () => console.log('WebSocket connected');
//   ws.onmessage = (event) => {
//     try {
//       const data = JSON.parse(event.data);
//       updateAxes(data); // expects {x, y, z}
//     } catch (e) {
//       console.error('WebSocket message error:', e);
//     }
//   };
//   ws.onclose = () => console.log('WebSocket closed');
//   ws.onerror = (err) => console.error('WebSocket error:', err);
// }

// setupWebSocket('ws://localhost:8080');

// Example usage: setupWebSocket('ws://localhost:8080');


// // 7. Handle window resize
// window.addEventListener('resize', () => {
//   camera.aspect = window.innerWidth / window.innerHeight;
//   camera.updateProjectionMatrix();
//   renderer.setSize(window.innerWidth, window.innerHeight);
// });

