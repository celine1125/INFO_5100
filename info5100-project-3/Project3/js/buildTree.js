// children: [Array of Node]
// data: {id: value}
// depth:
// parent:
// height:?

function stratify(nodes, data, group) {
  if(data.length<1) return {};
  if(!nodes.get(data[0][0]))
    nodes.set(data[0][0], Node(data[0][0]));
  for(var i=0; i<data.length; i++) {
    if(data[i].length>1) 
      append(nodes, data[i], group);
  }
  return nodes.get(data[0][0]);
}

function Node(id, group) {
  var node = {
    id: id
  }
  if(group) 
    node.group = group;
  return node;

}

function addChild(parent, child) {
  if(!parent.children)
    parent.children = [];
  parent.children.push(child);
  child.parent = parent;
}

function append(nodes, list, group) {
  var i = list.length-1;
  var preNode;
  var curNode;
  while(i>=0) {
    curNode = nodes.get(list[i]);
    if(curNode) {
      addChild(curNode, preNode);
      break;
    } else {
      if(i==list.length-1)
        nodes.set(list[i], Node(list[i], group));
      else
        nodes.set(list[i], Node(list[i]));
      curNode = nodes.get(list[i]);
      if(preNode)
        addChild(curNode, preNode);
      preNode = curNode;
    }
    i--;
  }
}


