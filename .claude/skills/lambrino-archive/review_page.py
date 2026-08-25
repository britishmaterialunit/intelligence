#!/usr/bin/env python3
"""Build a browsable review page from the manifest.

The TSV is what phase 2 reads, but 1,200 tab-separated rows are not something
anyone can actually review. This renders the same data as a filterable page —
search, filter by category / status / flag, and click through to the source
listing.

    python3 review_page.py --out _incoming/lambrino --html review.html
"""
import argparse, json, os, html, collections

PAGE = """<title>{title}</title>
<style>
  /* Extends the BMU archive's own palette: white ground, true-black hairlines,
     #222 ink, Helvetica. One oxide red, reserved for rows needing a decision. */
  :root {{
    --bg:#ffffff; --ink:#222222; --line:#000000; --rule:#d8d8d8;
    --faint:#f4f4f4; --muted:#8a8a8a; --flag:#8a3324; --link:#222222;
    --sans:Helvetica,Arial,sans-serif;
    --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg:#111111; --ink:#e9e9e9; --line:#e9e9e9; --rule:#333333;
      --faint:#1c1c1c; --muted:#8f8f8f; --flag:#d98269; --link:#e9e9e9;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg:#111111; --ink:#e9e9e9; --line:#e9e9e9; --rule:#333333;
    --faint:#1c1c1c; --muted:#8f8f8f; --flag:#d98269; --link:#e9e9e9;
  }}

  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font:15px/1.5 var(--sans); -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:1240px; margin:0 auto; padding:0 24px; }}

  header {{ border-bottom:2px solid var(--line); padding:36px 0 20px; }}
  h1 {{ margin:0; font-size:15px; font-weight:700;
    text-transform:uppercase; letter-spacing:.18em; }}
  .sub {{ margin-top:6px; font:12px/1.5 var(--mono); color:var(--muted); }}

  .stats {{ display:flex; flex-wrap:wrap; gap:0; margin-top:24px;
    border-top:1px solid var(--rule); }}
  .stat {{ flex:1 1 120px; padding:12px 16px 12px 0; }}
  .stat b {{ display:block; font:400 26px/1.1 var(--mono);
    font-variant-numeric:tabular-nums; }}
  .stat span {{ display:block; margin-top:4px; font-size:10px; color:var(--muted);
    text-transform:uppercase; letter-spacing:.12em; }}
  .stat.alert b {{ color:var(--flag); }}

  .controls {{ position:sticky; top:0; z-index:5; background:var(--bg);
    padding:14px 0; border-bottom:1px solid var(--line);
    display:flex; flex-wrap:wrap; gap:8px; align-items:center; }}
  input[type=search], select {{ font:13px/1 var(--sans); padding:8px 10px;
    border:1px solid var(--rule); border-radius:0;
    background:var(--bg); color:var(--ink); }}
  input[type=search] {{ flex:1 1 240px; }}
  input[type=search]:focus-visible, select:focus-visible {{
    outline:2px solid var(--flag); outline-offset:1px; }}
  .count {{ margin-left:auto; font:12px var(--mono); color:var(--muted);
    font-variant-numeric:tabular-nums; }}

  .scroll {{ overflow-x:auto; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{ text-align:left; font-size:10px; font-weight:700; color:var(--muted);
    text-transform:uppercase; letter-spacing:.12em;
    padding:12px 10px; border-bottom:1px solid var(--line); white-space:nowrap; }}
  td {{ padding:11px 10px; border-bottom:1px solid var(--rule); vertical-align:top; }}
  tbody tr:hover td {{ background:var(--faint); }}

  /* the stripe carries status, so a row needing a decision reads at a glance */
  td.lead {{ border-left:3px solid transparent; padding-left:13px; }}
  tr[data-status="check"] td.lead {{ border-left-color:var(--flag); }}
  tr[data-status="have"] td.lead {{ border-left-color:var(--ink); }}

  .name {{ font-size:14px; font-weight:700; }}
  .meta {{ margin-top:3px; font:11px var(--mono); color:var(--muted); }}
  .meta .st {{ text-transform:uppercase; letter-spacing:.08em; }}
  tr[data-status="check"] .meta .st {{ color:var(--flag); font-weight:700; }}
  .cat {{ font:12px var(--mono); color:var(--muted); white-space:nowrap; }}
  .n {{ font:13px var(--mono); font-variant-numeric:tabular-nums;
    text-align:right; color:var(--muted); }}
  .tag {{ display:inline-block; font:10px var(--mono); color:var(--muted);
    border:1px solid var(--rule); padding:2px 5px; margin:0 3px 3px 0;
    white-space:nowrap; }}
  .tag.rep {{ color:var(--flag); border-color:currentColor; }}
  .src {{ font-size:12px; color:var(--muted); max-width:34ch; }}
  .code {{ margin-top:2px; font:10px var(--mono); color:var(--muted);
    letter-spacing:.06em; }}
  a {{ color:var(--link); text-decoration:underline; text-underline-offset:2px; }}
  a:focus-visible {{ outline:2px solid var(--flag); outline-offset:2px; }}

  footer {{ border-top:1px solid var(--rule); margin-top:28px;
    padding:18px 0 48px; font:11px/1.7 var(--mono); color:var(--muted); }}
  @media (max-width:760px) {{ .hide-s {{ display:none; }} }}
</style>

<header><div class="wrap">
  <h1>{title}</h1>
  <div class="sub">{source} &mdash; {products} listings resolved to {garments} garments</div>
  <div class="stats">
    <div class="stat"><b>{garments}</b><span>Garments</span></div>
    <div class="stat"><b>{new}</b><span>New</span></div>
    <div class="stat alert"><b>{check}</b><span>Needs a call</span></div>
    <div class="stat"><b>{have}</b><span>Already held</span></div>
    <div class="stat alert"><b>{nodate}</b><span>Undated (0000s)</span></div>
    <div class="stat"><b>{gb}</b><span>GB projected</span></div>
  </div>
</div></header>

<div class="wrap">
  <div class="controls">
    <input type="search" id="q" placeholder="Search name or source listing" aria-label="Search garments">
    <select id="cat" aria-label="Filter by category"><option value="">All categories</option>{cats}</select>
    <select id="st" aria-label="Filter by status"><option value="">All statuses</option>{sts}</select>
    <select id="fl" aria-label="Filter by what needs attention">
      <option value="">Everything</option>{flagopts}
    </select>
    <span class="count" id="count"></span>
  </div>

  <div class="scroll"><table>
    <thead><tr>
      <th>Garment</th><th>Category</th><th class="n">Listings</th>
      <th class="hide-s">To resolve</th><th class="hide-s">Source listing</th>
    </tr></thead>
    <tbody id="tb">{rows}</tbody>
  </table></div>

  <footer>
    Names follow [Nation] [Division] [Date] [Detail] [Garment Type]. 0000s marks a date
    with no explicit marker in the listing &mdash; set it by hand in manifest.tsv.<br>
    Listings counts how many source listings collapsed into one garment. Edit
    manifest.tsv to change a name, category, or whether a garment is taken.
  </footer>
</div>

<script>
const rows = [...document.querySelectorAll('#tb tr')];
const q=document.getElementById('q'), cat=document.getElementById('cat'),
      st=document.getElementById('st'), fl=document.getElementById('fl'),
      count=document.getElementById('count');
function apply(){{
  const t=q.value.toLowerCase(), c=cat.value, s=st.value, f=fl.value;
  let n=0;
  for(const r of rows){{
    const ok = (!t || r.dataset.search.includes(t))
      && (!c || r.dataset.cat===c)
      && (!s || r.dataset.status===s)
      && (!f || (f==='__rep' ? r.dataset.replaces!=='' : r.dataset.flags.includes(f)));
    r.style.display = ok ? '' : 'none';
    if(ok) n++;
  }}
  count.textContent = n + ' of ' + rows.length;
}}
[q,cat,st,fl].forEach(e=>e.addEventListener('input',apply));
apply();
</script>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_incoming/lambrino")
    ap.add_argument("--html", default="review.html")
    ap.add_argument("--title", default="Lambrino Intake")
    ap.add_argument("--source", default="lambrino.co.uk / britain-uk")
    ap.add_argument("--per-kb", type=float, default=774.0,
                    help="measured KB per output image, for the size projection")
    a = ap.parse_args()

    rows = json.load(open(os.path.join(a.out, "manifest.json")))
    cats = sorted({r["cat"] for r in rows})
    sts = ["new", "check", "have"]

    body = []
    label = {"date-unknown": "date", "fabric-unknown": "fabric",
             "type-from-product-type": "garment type", "type-from-section": "garment type",
             "name-disambiguated": "name clash", "nation-forced": "nation assumed",
             "nation-mismatch": "nation mismatch", "variant-listing": "repeat listing"}
    for r in rows:
        notes = []
        if r["replaces"]:
            notes.append('<span class="tag rep">replaces '
                         f'{html.escape(r["replaces"])}</span>')
        for f in filter(None, r["flags"].split(",")):
            notes.append(f'<span class="tag">{html.escape(label.get(f, f))}</span>')
        search = (r["name"] + " " + r["source_title"]).lower().replace('"', "")
        body.append(
            f'<tr data-cat="{html.escape(r["cat"])}" data-status="{r["status"]}" '
            f'data-flags="{html.escape(r["flags"])}" data-replaces="{html.escape(r["replaces"])}" '
            f'data-search="{html.escape(search)}">'
            f'<td class="lead"><div class="name">{html.escape(r["name"])}</div>'
            f'<div class="meta"><span class="st">{r["status"]}</span></div></td>'
            f'<td class="cat">{html.escape(r["cat"])}</td>'
            f'<td class="n">{r["variants"]}</td>'
            f'<td class="hide-s">{"".join(notes)}</td>'
            f'<td class="hide-s src"><a href="{html.escape(r["url"])}" target="_blank" '
            f'rel="noopener">{html.escape(r["source_title"])}</a>'
            + (f'<div class="code">{html.escape(r["code"])}</div>' if r.get("code") else '')
            + '</td></tr>')

    flag_names = ["Needs a date", "Needs a fabric", "Garment type guessed",
                  "Name clash", "Nation assumed", "Nation mismatch", "Repeat listing"]
    flag_keys = ["date-unknown", "fabric-unknown", "type-from-product-type",
                 "name-disambiguated", "nation-forced", "nation-mismatch",
                 "variant-listing"]
    present = collections.Counter(f for r in rows for f in r["flags"].split(",") if f)
    if "type-from-section" in present:            # soframa's spelling of the same thing
        flag_keys[2] = "type-from-section"
    flagopts = "".join(
        f'<option value="{k}">{n} ({present[k]})</option>'
        for k, n in zip(flag_keys, flag_names) if present.get(k))
    if any(r["replaces"] for r in rows):
        flagopts += ('<option value="__rep">Supersedes an existing garment '
                     f'({sum(1 for r in rows if r["replaces"])})</option>')

    counts = collections.Counter(r["status"] for r in rows)
    n_inc = sum(1 for r in rows if r["include"] == "y")
    products = sum(int(r["variants"]) for r in rows)

    page = PAGE.format(
        title=html.escape(a.title), source=html.escape(a.source),
        products=products, garments=len(rows),
        new=counts["new"], check=counts["check"], have=counts["have"],
        nodate=sum(1 for r in rows if "date-unknown" in r["flags"]),
        gb=f"{n_inc * a.per_kb / 1024 / 1024:.2f}",
        cats="".join(f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in cats),
        sts="".join(f'<option value="{s}">{s}</option>' for s in sts),
        flagopts=flagopts,
        rows="".join(body))

    dest = os.path.join(a.out, a.html)
    open(dest, "w", encoding="utf-8").write(page)
    print(f"review page -> {dest} ({len(rows)} garments)")


if __name__ == "__main__":
    main()
