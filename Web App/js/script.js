import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';

function main() {

	const canvas = document.querySelector('#c');
	const renderer = new THREE.WebGLRenderer({ antialias: true, canvas });

	const fov = 45;
	const aspect = 2; // the canvas default
	const near = 0.1;
	const far = 100;
	const camera = new THREE.PerspectiveCamera(fov, aspect, near, far);
	camera.position.set(0, 10, 20);

	const controls = new OrbitControls(camera, canvas);
	controls.target.set(0, 5, 0);
	controls.update();

	const scene = new THREE.Scene();
	scene.background = new THREE.Color('black');

	/* {

		const planeSize = 40;

		const loader = new THREE.TextureLoader();
		const texture = loader.load( 'https://threejs.org/manual/examples/resources/images/checker.png' );
		texture.wrapS = THREE.RepeatWrapping;
		texture.wrapT = THREE.RepeatWrapping;
		texture.magFilter = THREE.NearestFilter;
		texture.colorSpace = THREE.SRGBColorSpace;
		const repeats = planeSize / 2;
		texture.repeat.set( repeats, repeats );

		const planeGeo = new THREE.PlaneGeometry( planeSize, planeSize );
		const planeMat = new THREE.MeshPhongMaterial( {
			map: texture,
			side: THREE.DoubleSide,
		} );
		const mesh = new THREE.Mesh( planeGeo, planeMat );
		mesh.rotation.x = Math.PI * - .5;
		scene.add( mesh );

	} */

	{

		const skyColor = 0xB1E1FF; // light blue
		const groundColor = 0xB97A20; // brownish orange
		const intensity = 2;
		const light = new THREE.HemisphereLight(skyColor, groundColor, intensity);
		scene.add(light);

	}

	{

		const color = 0xFFFFFF;
		const intensity = 2.5;
		const light = new THREE.DirectionalLight(color, intensity);
		light.position.set(5, 10, 2);
		scene.add(light);
		scene.add(light.target);

	}

	function frameArea(sizeToFitOnScreen, boxSize, boxCenter, camera) {

		const halfSizeToFitOnScreen = sizeToFitOnScreen * 0.5;
		const halfFovY = THREE.MathUtils.degToRad(camera.fov * .5);
		const distance = halfSizeToFitOnScreen / Math.tan(halfFovY);
		// compute a unit vector that points in the direction the camera is now
		// in the xz plane from the center of the box
		const direction = (new THREE.Vector3())
			.subVectors(camera.position, boxCenter)
			.multiply(new THREE.Vector3(1, 0, 1))
			.normalize();

		// move the camera to a position distance units way from the center
		// in whatever direction the camera was from the center already
		camera.position.copy(direction.multiplyScalar(distance).add(boxCenter));

		// pick some near and far values for the frustum that
		// will contain the box.
		camera.near = boxSize / 100;
		camera.far = boxSize * 100;

		camera.updateProjectionMatrix();

		// point the camera to look at the center of the box
		camera.lookAt(boxCenter.x, boxCenter.y, boxCenter.z);

	}

	{

		const gltfLoader = new GLTFLoader();
		gltfLoader.load('texturedMesh.glb', (gltf) => {

			const root = gltf.scene;
			scene.add(root);

			// compute the box that contains all the stuff
			// from root and below
			const box = new THREE.Box3().setFromObject(root);

			const boxSize = box.getSize(new THREE.Vector3()).length();
			const boxCenter = box.getCenter(new THREE.Vector3());

			// set the camera to frame the box
			frameArea(boxSize * 0.5, boxSize, boxCenter, camera);

			// update the Trackball controls to handle the new size
			controls.maxDistance = boxSize * 10;
			controls.target.copy(boxCenter);
			controls.update();

		});

	}

	function resizeRendererToDisplaySize(renderer) {

		const canvas = renderer.domElement;
		const width = canvas.clientWidth;
		const height = canvas.clientHeight;
		const needResize = canvas.width !== width || canvas.height !== height;
		if (needResize) {

			renderer.setSize(width, height, false);

		}

		return needResize;

	}

	function render() {

		if (resizeRendererToDisplaySize(renderer)) {

			const canvas = renderer.domElement;
			camera.aspect = canvas.clientWidth / canvas.clientHeight;
			camera.updateProjectionMatrix();

		}

		renderer.render(scene, camera);

		requestAnimationFrame(render);

	}

	requestAnimationFrame(render);

	// ---------- Annotation setup ----------
	const raycaster = new THREE.Raycaster();
	const mouse = new THREE.Vector2();
	const annotations = [];

	const labelsContainer = document.getElementById('labels');
	const inputBox = document.getElementById('annotationInput');
	const inputField = document.getElementById('annotationText');

	let pendingAnnotationPoint = null;

	canvas.addEventListener('click', onCanvasClick);

	function onCanvasClick(event) {
		const rect = canvas.getBoundingClientRect();

		mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
		mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

		raycaster.setFromCamera(mouse, camera);

		const intersects = raycaster.intersectObjects(scene.children, true);
		if (intersects.length === 0) return;

		pendingAnnotationPoint = intersects[0].point.clone();

		inputBox.style.left = `${event.clientX}px`;
		inputBox.style.top = `${event.clientY}px`;
		inputBox.hidden = false;

		inputField.value = '';
		inputField.focus();
	}

	inputField.addEventListener('keydown', (event) => {
		if (event.key === 'Enter') {
			confirmAnnotation();
		}
	});

	function confirmAnnotation() {
		const text = inputField.value.trim();
		if (!text || !pendingAnnotationPoint) return;

		addAnnotation(pendingAnnotationPoint, text);

		pendingAnnotationPoint = null;
		inputBox.hidden = true;
	}

	function addAnnotation(position, text) {
		const geometry = new THREE.SphereGeometry(0.1, 16, 16);
		const material = new THREE.MeshBasicMaterial({ color: 0xff0000 });
		const marker = new THREE.Mesh(geometry, material);

		marker.position.copy(position);
		scene.add(marker);

		const div = document.createElement('div');
		div.className = 'label';
		div.textContent = text;
		labelsContainer.appendChild(div);

		annotations.push({
			position: position.clone(),
			element: div
		});
	}

}

main();















// sidebar grab and drag function
const sidebar = document.getElementById("sidebar");
const handle = document.getElementById("resize-handle");
let isResizing = false;

handle.addEventListener("mousedown", () => {
	isResizing = true;
	document.body.style.cursor = "ew-resize";
});

document.addEventListener("mousemove", (e) => {
	if (!isResizing) return;

	const newWidth = e.clientX;
	sidebar.style.width = `${newWidth}px`;
});

document.addEventListener("mouseup", () => {
	isResizing = false;
	document.body.style.cursor = "default";
});
