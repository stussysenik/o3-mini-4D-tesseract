type Vec3 = [number, number, number];
type Vec4 = [number, number, number, number];

const targetId = "webgpu-hypertesseract-v1";
const locales = ["en"];
const limitations = [
  "Requires a browser with WebGPU enabled; unsupported browsers show a non-rendering fallback message.",
  "Glow is analytic and shader-based rather than full post-process bloom, so bright halos are stylized rather than physically accurate.",
  "The scene uses CPU-side 4D rotation and projection in TypeScript for compactness; larger topology or simulation workloads would justify GPU compute or WASM."
];

const app = document.getElementById("app") as HTMLDivElement;
const panel = document.getElementById("panel") as HTMLDivElement;
const fallback = document.getElementById("fallback") as HTMLDivElement;

const canvas = document.createElement("canvas");
app.appendChild(canvas);

let pointerX = 0;
let pointerY = 0;
window.addEventListener("pointermove", (event) => {
  pointerX = (event.clientX / innerWidth) * 2 - 1;
  pointerY = (event.clientY / innerHeight) * 2 - 1;
});

function setPanel(fps: string, status: string) {
  panel.innerHTML = `
    <div class="kicker">Benchmark Surface</div>
    <h1 class="title">Hypertesseract Benchmark v1</h1>
    <div class="grid">
      <div class="label">Target</div><div class="value">${targetId}</div>
      <div class="label">Runtime</div><div class="value">Browser WebGPU</div>
      <div class="label">Language</div><div class="value">TypeScript</div>
      <div class="label">Locale</div><div class="value">${locales.join(", ")}</div>
      <div class="label">WebGPU</div><div class="value">used directly</div>
      <div class="label">WASM</div><div class="value">not used</div>
      <div class="label">Status</div><div class="value">${status}</div>
      <div class="label">Frame</div><div class="value">${fps}</div>
    </div>
    <div class="footer">
      <span class="warn">Known limitations:</span> ${limitations[0]}
    </div>
  `;
}

function showFallback(message: string) {
  fallback.className = "fallback visible";
  fallback.textContent = message;
  setPanel("n/a", "WebGPU unavailable");
}

function mulMat4Vec4(m: Float32Array, v: [number, number, number, number]) {
  return [
    m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12] * v[3],
    m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13] * v[3],
    m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14] * v[3],
    m[3] * v[0] + m[7] * v[1] + m[11] * v[2] + m[15] * v[3]
  ] as [number, number, number, number];
}

function perspective(fovY: number, aspect: number, near: number, far: number) {
  const f = 1 / Math.tan(fovY * 0.5);
  const nf = 1 / (near - far);
  return new Float32Array([
    f / aspect, 0, 0, 0,
    0, f, 0, 0,
    0, 0, (far + near) * nf, -1,
    0, 0, (2 * far * near) * nf, 0
  ]);
}

function lookAt(eye: Vec3, center: Vec3, up: Vec3) {
  const zx = eye[0] - center[0];
  const zy = eye[1] - center[1];
  const zz = eye[2] - center[2];
  const zLen = Math.hypot(zx, zy, zz) || 1;
  const z0 = zx / zLen, z1 = zy / zLen, z2 = zz / zLen;

  const xx = up[1] * z2 - up[2] * z1;
  const xy = up[2] * z0 - up[0] * z2;
  const xz = up[0] * z1 - up[1] * z0;
  const xLen = Math.hypot(xx, xy, xz) || 1;
  const x0 = xx / xLen, x1 = xy / xLen, x2 = xz / xLen;

  const y0 = z1 * x2 - z2 * x1;
  const y1 = z2 * x0 - z0 * x2;
  const y2 = z0 * x1 - z1 * x0;

  return new Float32Array([
    x0, y0, z0, 0,
    x1, y1, z1, 0,
    x2, y2, z2, 0,
    -(x0 * eye[0] + x1 * eye[1] + x2 * eye[2]),
    -(y0 * eye[0] + y1 * eye[1] + y2 * eye[2]),
    -(z0 * eye[0] + z1 * eye[1] + z2 * eye[2]),
    1
  ]);
}

function rot4(a: Vec4, i: number, j: number, angle: number): Vec4 {
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  const out = [...a] as Vec4;
  out[i] = a[i] * c - a[j] * s;
  out[j] = a[i] * s + a[j] * c;
  return out;
}

const vertices4: Vec4[] = [];
for (let i = 0; i < 16; i++) {
  vertices4.push([
    (i & 1) ? 1 : -1,
    (i & 2) ? 1 : -1,
    (i & 4) ? 1 : -1,
    (i & 8) ? 1 : -1
  ]);
}

const edges: Array<[number, number]> = [];
for (let i = 0; i < 16; i++) {
  for (let bit = 0; bit < 4; bit++) {
    const j = i ^ (1 << bit);
    if (i < j) edges.push([i, j]);
  }
}

async function main() {
  if (!("gpu" in navigator)) {
    showFallback("WebGPU is not available in this browser. This benchmark intentionally does not provide a Canvas2D fallback because the target lane is direct WebGPU.");
    return;
  }

  const adapter = await navigator.gpu.requestAdapter();
  const device = adapter && await adapter.requestDevice();
  if (!device) {
    showFallback("Failed to acquire a WebGPU device. The benchmark remains honest about support and does not emulate the scene through another renderer.");
    return;
  }

  const context = canvas.getContext("webgpu");
  if (!context) {
    showFallback("The browser exposed navigator.gpu but did not provide a WebGPU canvas context.");
    return;
  }

  const format = navigator.gpu.getPreferredCanvasFormat();
  const quad = new Float32Array([
    -1, -1,
     1, -1,
    -1,  1,
    -1,  1,
     1, -1,
     1,  1
  ]);
  const quadBuffer = device.createBuffer({
    size: quad.byteLength,
    usage: GPUBufferUsage.VERTEX,
    mappedAtCreation: true
  });
  new Float32Array(quadBuffer.getMappedRange()).set(quad);
  quadBuffer.unmap();

  const instanceStride = 16 * 4;
  const segmentData = new Float32Array(edges.length * 16);
  const segmentBuffer = device.createBuffer({
    size: segmentData.byteLength,
    usage: GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST
  });

  const uniformBuffer = device.createBuffer({
    size: 64,
    usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST
  });

  const shader = device.createShaderModule({
    code: `
struct Uniforms {
  resolution: vec2<f32>,
  time: f32,
  glowScale: f32,
  tintA: vec4<f32>,
  tintB: vec4<f32>,
};
@group(0) @binding(0) var<uniform> u: Uniforms;

struct VSIn {
  @location(0) corner: vec2<f32>,
  @location(1) a0: vec4<f32>,
  @location(2) a1: vec4<f32>,
  @location(3) color: vec4<f32>,
  @location(4) lineMeta: vec4<f32>,
};

struct VSOut {
  @builtin(position) position: vec4<f32>,
  @location(0) uv: vec2<f32>,
  @location(1) color: vec4<f32>,
  @location(2) depthFade: f32,
};

@vertex
fn vsMain(input: VSIn) -> VSOut {
  let p0 = input.a0;
  let p1 = input.a1;
  let ndc0 = p0.xy / p0.w;
  let ndc1 = p1.xy / p1.w;
  let dir = normalize((ndc1 - ndc0) * vec2<f32>(u.resolution.x / max(u.resolution.y, 1.0), 1.0));
  let normal = vec2<f32>(-dir.y, dir.x);
  let width = input.lineMeta.x * (0.85 + u.glowScale * 0.25);
  let mixPos = mix(ndc0, ndc1, input.corner.x * 0.5 + 0.5);
  let clipW = mix(p0.w, p1.w, input.corner.x * 0.5 + 0.5);
  let offset = normal * input.corner.y * width / u.resolution.y * 2.0;
  var out: VSOut;
  out.position = vec4<f32>((mixPos + offset) * clipW, mix(p0.z / p0.w, p1.z / p1.w, input.corner.x * 0.5 + 0.5) * clipW, clipW);
  out.uv = input.corner;
  out.color = input.color;
  out.depthFade = input.lineMeta.y;
  return out;
}

@fragment
fn fsMain(input: VSOut) -> @location(0) vec4<f32> {
  let line = smoothstep(1.0, 0.08, abs(input.uv.y));
  let core = pow(line, 6.0);
  let halo = pow(line, 1.5) * 0.52;
  let pulse = 0.92 + 0.08 * sin(u.time * 1.3 + input.color.b * 4.0);
  let tint = mix(u.tintA, u.tintB, clamp(input.depthFade, 0.0, 1.0));
  let rgb = (input.color.rgb * (core * 1.6 + halo) + tint.rgb * halo * 0.55) * pulse;
  let alpha = clamp((core + halo) * input.color.a, 0.0, 1.0);
  return vec4<f32>(rgb, alpha);
}
`
  });

  const pipeline = device.createRenderPipeline({
    layout: "auto",
    vertex: {
      module: shader,
      entryPoint: "vsMain",
      buffers: [
        {
          arrayStride: 8,
          attributes: [{ shaderLocation: 0, format: "float32x2", offset: 0 }]
        },
        {
          arrayStride: instanceStride,
          stepMode: "instance",
          attributes: [
            { shaderLocation: 1, format: "float32x4", offset: 0 },
            { shaderLocation: 2, format: "float32x4", offset: 16 },
            { shaderLocation: 3, format: "float32x4", offset: 32 },
            { shaderLocation: 4, format: "float32x4", offset: 48 }
          ]
        }
      ]
    },
    fragment: {
      module: shader,
      entryPoint: "fsMain",
      targets: [{
        format,
        blend: {
          color: {
            srcFactor: "src-alpha",
            dstFactor: "one",
            operation: "add"
          },
          alpha: {
            srcFactor: "one",
            dstFactor: "one-minus-src-alpha",
            operation: "add"
          }
        }
      }]
    },
    primitive: {
      topology: "triangle-list",
      cullMode: "none"
    }
  });

  const bindGroup = device.createBindGroup({
    layout: pipeline.getBindGroupLayout(0),
    entries: [{ binding: 0, resource: { buffer: uniformBuffer } }]
  });

  function resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.floor(innerWidth * dpr));
    canvas.height = Math.max(1, Math.floor(innerHeight * dpr));
    canvas.style.width = `${innerWidth}px`;
    canvas.style.height = `${innerHeight}px`;
    context.configure({
      device,
      format,
      alphaMode: "premultiplied"
    });
  }
  resize();
  addEventListener("resize", resize);

  let last = performance.now();
  let acc = 0;
  let frames = 0;
  let fps = "measuring";

  setPanel(fps, "active");

  function frame(now: number) {
    const dt = Math.min((now - last) / 1000, 0.033);
    last = now;
    acc += dt;
    frames++;
    if (acc > 0.4) {
      fps = `${Math.round(frames / acc)} fps`;
      acc = 0;
      frames = 0;
    }

    const t = now * 0.001;
    const aspect = canvas.width / canvas.height;
    const proj = perspective(Math.PI / 3.2, aspect, 0.1, 40);
    const eye: Vec3 = [
      Math.sin(t * 0.24) * 6.4 + pointerX * 0.45,
      Math.sin(t * 0.18) * 1.2 - pointerY * 0.4,
      7.4
    ];
    const view = lookAt(eye, [0, 0, 0], [0, 1, 0]);

    for (let e = 0; e < edges.length; e++) {
      const [ia, ib] = edges[e];
      let a = vertices4[ia];
      let b = vertices4[ib];

      a = rot4(a, 0, 3, t * 0.48);
      a = rot4(a, 1, 2, t * 0.36);
      a = rot4(a, 0, 2, t * 0.17 + pointerX * 0.35);
      a = rot4(a, 1, 3, t * 0.14 - pointerY * 0.28);

      b = rot4(b, 0, 3, t * 0.48);
      b = rot4(b, 1, 2, t * 0.36);
      b = rot4(b, 0, 2, t * 0.17 + pointerX * 0.35);
      b = rot4(b, 1, 3, t * 0.14 - pointerY * 0.28);

      const wa = 4.1 / (4.6 - a[3]);
      const wb = 4.1 / (4.6 - b[3]);

      const a3: [number, number, number, number] = [a[0] * wa * 1.3, a[1] * wa * 1.3, a[2] * wa * 1.3, 1];
      const b3: [number, number, number, number] = [b[0] * wb * 1.3, b[1] * wb * 1.3, b[2] * wb * 1.3, 1];

      const va = mulMat4Vec4(view, a3);
      const vb = mulMat4Vec4(view, b3);
      const pa = mulMat4Vec4(proj, va);
      const pb = mulMat4Vec4(proj, vb);

      const lum = Math.max(0.18, 0.9 - ((va[2] + vb[2]) * -0.06));
      const chroma = 0.45 + (wa + wb) * 0.09;
      const depthFade = Math.max(0, Math.min(1, 1 - ((-va[2] + -vb[2]) * 0.06)));
      const width = 2.8 + (wa + wb) * 0.9;

      const o = e * 16;
      segmentData.set(pa, o + 0);
      segmentData.set(pb, o + 4);
      segmentData[o + 8] = 0.42 * lum;
      segmentData[o + 9] = 0.78 * chroma;
      segmentData[o + 10] = 1.12 * lum;
      segmentData[o + 11] = 0.42;
      segmentData[o + 12] = width;
      segmentData[o + 13] = depthFade;
      segmentData[o + 14] = wa;
      segmentData[o + 15] = wb;
    }

    device.queue.writeBuffer(segmentBuffer, 0, segmentData);

    const uniforms = new Float32Array([
      canvas.width, canvas.height, t, 1 + Math.abs(pointerX) * 0.5,
      0.06, 0.42, 0.54, 1,
      0.48, 0.92, 1.18, 1,
      0, 0, 0, 0
    ]);
    device.queue.writeBuffer(uniformBuffer, 0, uniforms);

    const encoder = device.createCommandEncoder();
    const textureView = context.getCurrentTexture().createView();
    const pass = encoder.beginRenderPass({
      colorAttachments: [{
        view: textureView,
        clearValue: {
          r: 0.018 + Math.max(pointerY, 0) * 0.01,
          g: 0.038,
          b: 0.058 + Math.max(pointerX, 0) * 0.015,
          a: 1
        },
        loadOp: "clear",
        storeOp: "store"
      }]
    });

    pass.setPipeline(pipeline);
    pass.setBindGroup(0, bindGroup);
    pass.setVertexBuffer(0, quadBuffer);
    pass.setVertexBuffer(1, segmentBuffer);
    pass.draw(6, edges.length);
    pass.end();

    device.queue.submit([encoder.finish()]);
    setPanel(fps, "active");
    requestAnimationFrame(frame);
  }

  requestAnimationFrame(frame);
}

main();
