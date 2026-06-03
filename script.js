const data = {"volumes": [{"name": "WorldBox", "vertices": [-500.0, -500.0, -500.0, 500.0, -500.0, -500.0, 500.0, 500.0, -500.0, -500.0, 500.0, -500.0, -500.0, -500.0, 500.0, -500.0, 500.0, 500.0, 500.0, 500.0, 500.0, 500.0, -500.0, 500.0, -500.0, -500.0, -500.0, -500.0, -500.0, 500.0, 500.0, -500.0, 500.0, 500.0, -500.0, -500.0, 500.0, 500.0, -500.0, 500.0, 500.0, 500.0, -500.0, 500.0, 500.0, -500.0, 500.0, -500.0, -500.0, -500.0, -500.0, -500.0, 500.0, -500.0, -500.0, 500.0, 500.0, -500.0, -500.0, 500.0, 500.0, -500.0, -500.0, 500.0, -500.0, 500.0, 500.0, 500.0, 500.0, 500.0, 500.0, -500.0], "indices": [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 8, 9, 10, 8, 10, 11, 12, 13, 14, 12, 14, 15, 16, 17, 18, 16, 18, 19, 20, 21, 22, 20, 22, 23], "position": [0.0, 0.0, 0.0]}]};

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100000);
camera.position.set(0, 0, 2000);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(500, 500);
renderer.setClearColor(0x0a0a10);
document.body.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0xffffff, 0.4));
const dl = new THREE.DirectionalLight(0xffffff, 0.8);
dl.position.set(1, 1, 1);
scene.add(dl);

const colors = [0x378ADD, 0x5DCAA5, 0xEF9F27];

data.volumes.forEach((vol, i) => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position",
        new THREE.Float32BufferAttribute(vol.vertices, 3));
    geo.setIndex(vol.indices);
    geo.computeVertexNormals();

    const mat = new THREE.MeshPhongMaterial({
        color: colors[i % colors.length],
        transparent: true,
        opacity: 0.7,
        side: THREE.DoubleSide
    });

    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(...vol.position);
    scene.add(mesh);

    scene.add(new THREE.LineSegments(
        new THREE.EdgesGeometry(geo),
        new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.3, transparent: true })
    ));
});

let drag = false, px = 0, py = 0;
renderer.domElement.addEventListener("mousedown", e => { drag=true; px=e.clientX; py=e.clientY; });
renderer.domElement.addEventListener("mouseup", () => drag=false);
renderer.domElement.addEventListener("mousemove", e => {
    if (!drag) return;
    scene.rotation.y += (e.clientX - px) * 0.005;
    scene.rotation.x += (e.clientY - py) * 0.005;
    px=e.clientX; py=e.clientY;
});
renderer.domElement.addEventListener("wheel", e => {
    camera.position.z += e.deltaY * 0.5;
});

(function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
})();
