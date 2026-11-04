// Minimal, non-recursive Newick parser and a rectangular tree layout.

export interface TreeNode {
  name: string;
  length: number;
  children: TreeNode[];
}

/** Parse a Newick string. Iterative, so very deep trees do not overflow the stack. */
export function parseNewick(text: string): TreeNode {
  const s = text.trim().replace(/;\s*$/, "");
  const stack: TreeNode[] = [];
  let current: TreeNode | null = null; // node that a following label/length belongs to
  let root: TreeNode | null = null;
  let i = 0;

  const newNode = (): TreeNode => ({ name: "", length: 0, children: [] });

  while (i < s.length) {
    const ch = s[i];
    if (ch === "(") {
      const node = newNode();
      if (stack.length) stack[stack.length - 1].children.push(node);
      stack.push(node);
      current = null;
      i++;
    } else if (ch === ",") {
      current = null;
      i++;
    } else if (ch === ")") {
      current = stack.pop() ?? null;
      root = current;
      i++;
    } else if (ch === ":") {
      i++;
      let j = i;
      while (j < s.length && !",():;".includes(s[j])) j++;
      const value = parseFloat(s.slice(i, j));
      if (current) current.length = Number.isFinite(value) ? Math.max(value, 0) : 0;
      i = j;
    } else {
      let j = i;
      while (j < s.length && !",():;".includes(s[j])) j++;
      const label = s.slice(i, j).trim();
      if (current === null) {
        // a new leaf
        const leaf = newNode();
        leaf.name = label;
        if (stack.length) stack[stack.length - 1].children.push(leaf);
        else root = leaf;
        current = leaf;
      } else {
        current.name = label; // label of an inner node
      }
      i = j;
    }
  }
  if (!root) throw new Error("Boş Newick ağacı");
  return root;
}

export interface LaidOutNode {
  node: TreeNode;
  parent: number; // index in `nodes`, -1 for the root
  x: number;
  y: number;
  depth: number; // number of edges from the root
  isLeaf: boolean;
  leafIndex: number; // row of the leaf, -1 for inner nodes
}

export interface TreeLayout {
  nodes: LaidOutNode[];
  leaves: number[]; // indices in `nodes`, top to bottom
  maxX: number;
  rowHeight: number;
  hasBranchLengths: boolean;
  usesLengths: boolean; // true when x is drawn proportional to branch length
  span: number; // branch-length (or depth) value that corresponds to `maxX`
}

/**
 * Rectangular layout. mode "phylogram": x = summed branch lengths; "cladogram": x = depth.
 * Leaves get equal vertical spacing (rowHeight); inner nodes sit in the middle of their children.
 */
export function layoutTree(
  root: TreeNode,
  mode: "phylogram" | "cladogram",
  width: number,
  rowHeight = 14,
): TreeLayout {
  const nodes: LaidOutNode[] = [];
  // preorder walk with an explicit stack
  const todo: { node: TreeNode; parent: number; depth: number; dist: number }[] = [
    { node: root, parent: -1, depth: 0, dist: 0 },
  ];
  const order: number[] = [];
  while (todo.length) {
    const t = todo.pop()!;
    const idx = nodes.length;
    nodes.push({
      node: t.node,
      parent: t.parent,
      x: t.dist,
      y: 0,
      depth: t.depth,
      isLeaf: t.node.children.length === 0,
      leafIndex: -1,
    });
    order.push(idx);
    // push children in reverse so that they are visited in their original order
    for (let k = t.node.children.length - 1; k >= 0; k--) {
      const c = t.node.children[k];
      todo.push({ node: c, parent: idx, depth: t.depth + 1, dist: t.dist + c.length });
    }
  }

  const leaves: number[] = [];
  for (const idx of order) {
    if (nodes[idx].isLeaf) {
      nodes[idx].leafIndex = leaves.length;
      nodes[idx].y = leaves.length * rowHeight;
      leaves.push(idx);
    }
  }
  // inner node y = mean of the first and last child (children come after parents in `order`)
  const childrenOf: number[][] = nodes.map(() => []);
  nodes.forEach((n, i) => {
    if (n.parent >= 0) childrenOf[n.parent].push(i);
  });
  for (let k = order.length - 1; k >= 0; k--) {
    const idx = order[k];
    if (!nodes[idx].isLeaf) {
      const ch = childrenOf[idx];
      nodes[idx].y = (nodes[ch[0]].y + nodes[ch[ch.length - 1]].y) / 2;
    }
  }

  let maxLen = 0;
  let maxDepth = 0;
  for (const n of nodes) {
    maxLen = Math.max(maxLen, n.x);
    maxDepth = Math.max(maxDepth, n.depth);
  }
  const hasBranchLengths = maxLen > 0;
  const useLengths = mode === "phylogram" && hasBranchLengths;
  const span = useLengths ? maxLen : Math.max(maxDepth, 1);
  for (const n of nodes) {
    n.x = ((useLengths ? n.x : n.depth) / span) * width;
  }
  return { nodes, leaves, maxX: width, rowHeight, hasBranchLengths, usesLengths: useLengths, span };
}

/** 'Quercus_robur__KX123456.1' -> { species: 'Quercus robur', accession: 'KX123456.1' } */
export function parseLeafLabel(label: string): { species: string; accession: string } {
  const [sp, acc = ""] = label.split("__");
  return { species: sp.replace(/_/g, " "), accession: acc };
}
