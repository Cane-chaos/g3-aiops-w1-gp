import re

with open('docs/g3-lab-presentation.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The slide to replace
target_slide_regex = r'  <section class="slide">\n    <div class="wrap full">\n      <div class="eyebrow">Structural Break</div>\n      <h2 style="color: var\(--red\); margin-bottom: 0\.5rem;">Incident Matrix: The Collapse of Correlation</h2>.*?<div class="footer"><span>Correlation Collapse</span><span>Isolation Boundaries</span></div>\n  </section>'

new_slides = """  <section class="slide">
    <div class="wrap full">
      <div class="eyebrow">Structural Break</div>
      <h2 style="color: var(--red); margin-bottom: 0.5rem;">Baseline Correlation (Full Day)</h2>
      <p class="sublead" style="margin-bottom: 2rem;">The normal state of the system manifold before the incident window.</p>

      <div style="display: flex; justify-content: center;">
        <img src="assets/g3/exhaustive_full_day_correlation.png" alt="Full Day Correlation" style="width: 100%; max-height: 65vh; object-fit: contain; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);" />
      </div>
    </div>
    <div class="footer"><span>Correlation Collapse</span><span>Full Day Baseline</span></div>
  </section>

  <section class="slide">
    <div class="wrap full">
      <div class="eyebrow">Structural Break</div>
      <h2 style="color: var(--red); margin-bottom: 0.5rem;">Incident Matrix: The Collapse of Correlation</h2>
      <p class="sublead" style="margin-bottom: 2rem;">Mapping the structural break to configure high-confidence isolation boundaries.</p>

      <div style="display: flex; gap: 2rem; align-items: center;">
        <div style="flex: 1.2;">
            <img src="assets/g3/exhaustive_incident_correlation.png" alt="Incident Correlation" style="width: 100%; max-height: 60vh; object-fit: contain; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);" />
        </div>

        <div style="flex: 1; display: flex; flex-direction: column; gap: 1.5rem;">
          <div style="background: var(--soft); padding: 1.5rem; border-radius: 8px; border-left: 4px solid var(--red);">
            <h3 style="margin-top: 0; color: var(--ink);">Decoupling &amp; Inversion</h3>
            <p style="color: var(--muted); font-size: 15px; line-height: 1.6; margin: 0;">
              During the incident window, the predictable baseline manifold shatters. Notice how historically
              synchronized metrics suddenly show zero or inverse correlation (e.g., traffic drops abruptly
              while latency or error rates spike to saturation). 
              <br>The linear relationship Y &asymp; mX + c is
              violently violated.
            </p>
          </div>
          <div style="background: var(--soft); padding: 1.5rem; border-radius: 8px; border-left: 4px solid var(--blue);">
            <h3 style="margin-top: 0; color: var(--ink);">Optimizing iForest Sensitivity</h3>
            <p style="color: var(--muted); font-size: 15px; line-height: 1.6; margin: 0;">
              This structural break is exactly what the Isolation Forest thrives on. When data points violate
              the normal correlation plane, they are cast into sparse, unpopulated regions of the
              high-dimensional space. The iForest can easily slice these outliers with <strong>exceptionally
              short path lengths</strong>, yielding anomaly scores approaching 1.0.
            </p>
          </div>
        </div>
      </div>
    </div>
    <div class="footer"><span>Correlation Collapse</span><span>Incident Window</span></div>
  </section>

  <section class="slide">
    <div class="wrap full">
      <div style="display: flex; justify-content: center; width: 100%; height: 100%;">
        <img src="../figures/2aoboqbml8d2mfqnybco79qqlrig5z2l4kbkclrs3.jpg" style="width: 100%; max-height: 85vh; object-fit: contain;" />
      </div>
    </div>
  </section>
  <section class="slide">
    <div class="wrap full">
      <div style="display: flex; justify-content: center; width: 100%; height: 100%;">
        <img src="../figures/2aoboqbml8huqybnxvaumxfixcdept9q4gcmbwmc5.jpg" style="width: 100%; max-height: 85vh; object-fit: contain;" />
      </div>
    </div>
  </section>
  <section class="slide">
    <div class="wrap full">
      <div style="display: flex; justify-content: center; width: 100%; height: 100%;">
        <img src="../figures/2aoboqbml8mqw4pzo5iz9qddiekechv64qtnlzh62.jpg" style="width: 100%; max-height: 85vh; object-fit: contain;" />
      </div>
    </div>
  </section>
  <section class="slide">
    <div class="wrap full">
      <div style="display: flex; justify-content: center; width: 100%; height: 100%;">
        <img src="../figures/2aoboqbml8vjynw7oh1aol1emehuypofecmjyuqw1.jpg" style="width: 100%; max-height: 85vh; object-fit: contain;" />
      </div>
    </div>
  </section>
  <section class="slide">
    <div class="wrap full">
      <div style="display: flex; justify-content: center; width: 100%; height: 100%;">
        <img src="../figures/2aoboqbml99uya8iou2ndvcut7o0zaj3icx4gyow4.jpg" style="width: 100%; max-height: 85vh; object-fit: contain;" />
      </div>
    </div>
  </section>"""

new_content = re.sub(target_slide_regex, new_slides, content, flags=re.DOTALL)

with open('docs/g3-lab-presentation.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Slides updated successfully.")
