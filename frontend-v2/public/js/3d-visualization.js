/**
 * SMARTII 3D Holographic Visualization
 * Three.js powered AI sphere with particle effects
 */

import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.159.0/build/three.module.js';

class HolographicSphere {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Container not found:', containerId);
            return;
        }
        
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.sphere = null;
        this.particles = null;
        this.animationId = null;
        this.isAnimating = false;
        this.audioData = new Uint8Array(128);
        
        this.init();
    }
    
    init() {
        // Scene setup
        this.scene = new THREE.Scene();
        
        // Camera setup
        this.camera = new THREE.PerspectiveCamera(
            75,
            this.container.offsetWidth / this.container.offsetHeight,
            0.1,
            1000
        );
        this.camera.position.z = 5;
        
        // Renderer setup
        this.renderer = new THREE.WebGLRenderer({ 
            alpha: true, 
            antialias: true 
        });
        this.renderer.setSize(this.container.offsetWidth, this.container.offsetHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);
        
        // Create holographic sphere
        this.createHolographicSphere();
        
        // Create particle system
        this.createParticles();
        
        // Create energy rings
        this.createEnergyRings();
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 2);
        this.scene.add(ambientLight);
        
        const pointLight = new THREE.PointLight(0x00d9ff, 2, 100);
        pointLight.position.set(0, 0, 10);
        this.scene.add(pointLight);
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Start animation
        this.animate();
    }
    
    createHolographicSphere() {
        // Wireframe sphere
        const geometry = new THREE.SphereGeometry(1.5, 32, 32);
        const material = new THREE.MeshBasicMaterial({
            color: 0x00d9ff,
            wireframe: true,
            transparent: true,
            opacity: 0.3
        });
        
        this.sphere = new THREE.Mesh(geometry, material);
        this.scene.add(this.sphere);
        
        // Inner glow sphere
        const glowGeometry = new THREE.SphereGeometry(1.45, 32, 32);
        const glowMaterial = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                color: { value: new THREE.Color(0x00d9ff) }
            },
            vertexShader: `
                varying vec3 vNormal;
                void main() {
                    vNormal = normalize(normalMatrix * normal);
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform float time;
                uniform vec3 color;
                varying vec3 vNormal;
                void main() {
                    float intensity = pow(0.7 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
                    float pulse = sin(time * 2.0) * 0.3 + 0.7;
                    gl_FragColor = vec4(color, intensity * pulse);
                }
            `,
            transparent: true,
            blending: THREE.AdditiveBlending
        });
        
        this.glowSphere = new THREE.Mesh(glowGeometry, glowMaterial);
        this.scene.add(this.glowSphere);
    }
    
    createParticles() {
        const particleCount = 1000;
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);
        
        for (let i = 0; i < particleCount; i++) {
            // Random position in sphere
            const radius = 3 + Math.random() * 2;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos((Math.random() * 2) - 1);
            
            positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i * 3 + 2] = radius * Math.cos(phi);
            
            // Color gradient (cyan to blue)
            const color = new THREE.Color();
            color.setHSL(0.5 + Math.random() * 0.1, 1.0, 0.5 + Math.random() * 0.3);
            colors[i * 3] = color.r;
            colors[i * 3 + 1] = color.g;
            colors[i * 3 + 2] = color.b;
        }
        
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        
        const material = new THREE.PointsMaterial({
            size: 0.05,
            vertexColors: true,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending
        });
        
        this.particles = new THREE.Points(geometry, material);
        this.scene.add(this.particles);
    }
    
    createEnergyRings() {
        this.rings = [];
        const ringCount = 3;
        
        for (let i = 0; i < ringCount; i++) {
            const geometry = new THREE.TorusGeometry(2 + i * 0.3, 0.02, 16, 100);
            const material = new THREE.MeshBasicMaterial({
                color: 0x00d9ff,
                transparent: true,
                opacity: 0.3
            });
            
            const ring = new THREE.Mesh(geometry, material);
            ring.rotation.x = Math.PI / 2;
            ring.userData.rotationSpeed = 0.001 * (i + 1);
            
            this.rings.push(ring);
            this.scene.add(ring);
        }
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        const time = Date.now() * 0.001;
        
        // Rotate sphere
        if (this.sphere) {
            this.sphere.rotation.x += 0.003;
            this.sphere.rotation.y += 0.005;
        }
        
        // Update glow
        if (this.glowSphere) {
            this.glowSphere.material.uniforms.time.value = time;
            this.glowSphere.rotation.x += 0.002;
            this.glowSphere.rotation.y += 0.003;
        }
        
        // Rotate particles
        if (this.particles) {
            this.particles.rotation.y += 0.0005;
            
            // Pulse effect
            const positions = this.particles.geometry.attributes.position.array;
            for (let i = 0; i < positions.length; i += 3) {
                const distance = Math.sqrt(
                    positions[i] ** 2 + 
                    positions[i + 1] ** 2 + 
                    positions[i + 2] ** 2
                );
                const wave = Math.sin(time * 2 + distance * 0.5) * 0.1;
                positions[i + 1] += wave * 0.01;
            }
            this.particles.geometry.attributes.position.needsUpdate = true;
        }
        
        // Rotate energy rings
        if (this.rings) {
            this.rings.forEach(ring => {
                ring.rotation.z += ring.userData.rotationSpeed;
            });
        }
        
        this.renderer.render(this.scene, this.camera);
    }
    
    updateAudioData(dataArray) {
        if (!this.sphere) return;
        
        // React to audio input
        const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        const scale = 1 + (average / 255) * 0.5;
        
        this.sphere.scale.set(scale, scale, scale);
        
        if (this.glowSphere) {
            this.glowSphere.scale.set(scale * 0.95, scale * 0.95, scale * 0.95);
        }
    }
    
    setActive(active) {
        this.isAnimating = active;
        
        if (this.sphere) {
            const targetOpacity = active ? 0.6 : 0.3;
            this.sphere.material.opacity = targetOpacity;
        }
        
        if (this.particles) {
            const targetOpacity = active ? 0.8 : 0.6;
            this.particles.material.opacity = targetOpacity;
        }
    }
    
    onWindowResize() {
        if (!this.container) return;
        
        this.camera.aspect = this.container.offsetWidth / this.container.offsetHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.offsetWidth, this.container.offsetHeight);
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.renderer) {
            this.renderer.dispose();
            this.container.removeChild(this.renderer.domElement);
        }
        
        window.removeEventListener('resize', this.onWindowResize);
    }
}

// Export for use in main script
window.HolographicSphere = HolographicSphere;
