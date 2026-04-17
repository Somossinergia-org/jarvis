import pathlib
h = pathlib.Path("static/index.html").read_text(encoding="utf-8")

# Fix dimming of main nodes (use nd.pts not nd._cloud)
old1 = "if (n._cloud && n._cloud.material) {\n      n._cloud.material.opacity = 0.12;\n    }"
new1 = "if (n.pts && n.pts.material) { n.pts.material.opacity = 0.08; }"
if old1 in h:
    h = h.replace(old1, new1)
    print("dim fix applied")
else:
    print("dim: searching alternate")
    old1b = "if (n._cloud && n._cloud.material) {"
    if old1b in h:
        idx = h.find(old1b)
        end = h.find("}", idx) + 1
        h = h[:idx] + "if (n.pts && n.pts.material) { n.pts.material.opacity = 0.08; }" + h[end:]
        print("dim fix applied (fallback)")

old2 = "if (n._cloud && n._cloud.material) n._cloud.material.opacity = 0.9;"
new2 = "if (n.pts && n.pts.material) n.pts.material.opacity = 0.9;"
if old2 in h:
    h = h.replace(old2, new2)
    print("restore fix applied")
else:
    print("restore: not found, trying pattern")
    h = h.replace(
        "n._cloud.material.opacity = 0.9",
        "n.pts && n.pts.material ? n.pts.material.opacity = 0.9 : null"
    )

pathlib.Path("static/index.html").write_text(h, encoding="utf-8")
print("DONE:", len(h))
