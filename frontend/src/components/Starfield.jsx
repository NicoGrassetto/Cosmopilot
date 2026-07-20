import { useEffect, useRef } from 'react';

// A lightweight canvas starfield: many twinkling drifting stars plus a few large
// blurred "planet" orbs that slowly float. Purely decorative and non-interactive.
export default function Starfield() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let raf;
    let width = 0;
    let height = 0;
    // Render at full device pixel ratio (capped at 3) so particles stay crisp
    // on high-DPI / Retina displays instead of looking soft.
    const dpr = Math.min(window.devicePixelRatio || 1, 3);

    let stars = [];
    let planets = [];

    function seed() {
      // Denser field of finer stars for a higher-resolution look.
      const count = Math.floor((width * height) / 2600);
      stars = Array.from({ length: count }, () => {
        // Mostly tiny pin-sharp stars, with a few slightly larger, brighter ones.
        const big = Math.random() < 0.12;
        return {
          x: Math.random() * width,
          y: Math.random() * height,
          r: big ? Math.random() * 1.1 + 0.9 : Math.random() * 0.7 + 0.35,
          vx: (Math.random() - 0.5) * 0.05,
          vy: (Math.random() - 0.5) * 0.05,
          tw: Math.random() * Math.PI * 2, // twinkle phase
          ts: Math.random() * 0.02 + 0.005, // twinkle speed
          glow: big,
        };
      });

      const palette = [
        ['#6d5efc', '#241b57'],
        ['#3b82f6', '#0b2447'],
        ['#a855f7', '#2a1052'],
        ['#f59e0b', '#3a2606'],
      ];
      planets = Array.from({ length: 4 }, (_, i) => {
        const [c1, c2] = palette[i % palette.length];
        return {
          x: Math.random() * width,
          y: Math.random() * height,
          r: Math.random() * 120 + 80,
          vx: (Math.random() - 0.5) * 0.12,
          vy: (Math.random() - 0.5) * 0.12,
          c1,
          c2,
        };
      });
    }

    function resize() {
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      seed();
    }

    function wrap(p) {
      if (p.x < -p.r) p.x = width + p.r;
      if (p.x > width + p.r) p.x = -p.r;
      if (p.y < -p.r) p.y = height + p.r;
      if (p.y > height + p.r) p.y = -p.r;
    }

    function frame() {
      // Paint an explicit deep-space background so the canvas is never
      // transparent (which can render as white on top of some compositors).
      ctx.globalAlpha = 1;
      ctx.fillStyle = '#04040a';
      ctx.fillRect(0, 0, width, height);

      // Planets — big, soft, slow radial glows.
      for (const pl of planets) {
        pl.x += pl.vx;
        pl.y += pl.vy;
        wrap(pl);
        const g = ctx.createRadialGradient(pl.x, pl.y, 0, pl.x, pl.y, pl.r);
        g.addColorStop(0, pl.c1);
        g.addColorStop(1, 'transparent');
        ctx.globalAlpha = 0.35;
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(pl.x, pl.y, pl.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      // Stars — tiny drifting twinkles, drawn crisp at full DPR.
      for (const s of stars) {
        s.x += s.vx;
        s.y += s.vy;
        s.tw += s.ts;
        wrap(s);
        const alpha = 0.45 + Math.sin(s.tw) * 0.4;
        ctx.globalAlpha = Math.max(0, alpha);
        if (s.glow) {
          ctx.shadowColor = 'rgba(255,255,255,0.9)';
          ctx.shadowBlur = 6;
        } else {
          ctx.shadowBlur = 0;
        }
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;

      raf = requestAnimationFrame(frame);
    }

    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    resize();
    window.addEventListener('resize', resize);
    if (reduce) {
      frame(); // draw one static frame
      cancelAnimationFrame(raf);
    } else {
      frame();
    }

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return <canvas ref={canvasRef} className="starfield" aria-hidden="true" />;
}
