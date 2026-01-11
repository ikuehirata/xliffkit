


# Examples

This page shows concise before/after snapshots for the sample projects in the repository's `examples/` directory.
Each example focuses on "what changes" and intentionally omits detailed CLI or step-by-step instructions.


## 01_fix_ph_to_bpt_ept

- Description: Convert anonymous `ph` tags that wrap formatting (e.g. bold/italic) into structured start/end tags such as `bpt`/`ept`.
- Expected benefit: Restored structure improves portability for serializers and translation tools.
- Directory: [examples/01_fix_ph_to_bpt_ept](../../examples/01_fix_ph_to_bpt_ept)

<div style="display:flex; gap:1rem; align-items:flex-start;">
  <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:0.5rem;">
  <b style="margin:0; padding:0; align-self:center;">Before</b>
  <img src="images/01_fix_before.png" alt="01-before" style="max-width:100%; width:540px; display:block; margin:0; vertical-align:top;" />
  </div>
  <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:0.5rem;">
  <b style="margin:0; padding:0; align-self:center;">After</b>
  <img src="images/01_fix_after.png" alt="01-after" style="max-width:100%; width:540px; display:block; margin:0; vertical-align:top;" />
  </div>
</div>

## 02_split

- Description: Split long segments at sentence boundaries while preserving inline tag integrity, producing multiple TUs suitable for sentence-level editing.
- Expected benefit: More uniform translation units; may improve matches against translation memory.
- Directory: [examples/02_split](../../examples/02_split)

<div style="display:flex; gap:1rem; align-items:flex-start;">
  <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:0.5rem;">
  <b style="margin:0; padding:0; align-self:center;">Before</b>
  <img src="images/02_split_before.png" alt="02-before" style="max-width:100%; width:540px; display:block; margin:0; vertical-align:top;" />
  </div>
  <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:0.5rem;">
  <b style="margin:0; padding:0; align-self:center;">After</b>
  <img src="images/02_split_after.png" alt="02-after" style="max-width:100%; width:540px; display:block; margin:0; vertical-align:top;" />
  </div>
</div>


## 03_merge

- Description: Recombine multiple split TUs based on context ID, renumber tag IDs and adjust flattened representations to restore the original grouping.
- Expected benefit: Produce consistent TUs after a split→edit→merge workflow.
- Directory: [examples/03_merge](../../examples/03_merge)

<div style="display:flex; gap:1rem; align-items:flex-start;">
  <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:0.5rem;">
  <b style="margin:0; padding:0; align-self:center;">Before</b>
  <img src="images/03_merge_before.png" alt="03-before" style="max-width:100%; width:540px; display:block; margin:0; vertical-align:top;" />
  </div>
  <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:0.5rem;">
  <b style="margin:0; padding:0; align-self:center;">After</b>
  <img src="images/03_merge_after.png" alt="03-after" style="max-width:100%; width:540px; display:block; margin:0; vertical-align:top;" />
  </div>
</div>

