var path = require('path');

var TreeNode = function(id) {
  this.id = id;
  this.parent = path.dirname(id);
  this.name = path.basename(id);
  this.kids = [];
}

TreeNode.prototype.generateHtml = function() {
  var html = '';

  html += '<li>\n';
  html += '  <input type="checkbox" checked="checked" id="' + this.name + '" />\n';
  html += '  <label for="' + this.name + '">' + this.name + '</label>\n';

  if (this.kids.length > 0) {
    html += '    <ul>\n';
    for(var i in this.kids) {
      html += this.kids[i].generateHtml();
    }
    html += '    </ul>\n';
  }

  html += '</li>\n';

  return html;
}

var LeafNode = function(asset) {
  this.id = asset.name;
  this.parent = path.dirname(asset.name);
  this.name = path.basename(asset.name);
  this.url = '/view/' + asset.xlink;
}

LeafNode.prototype = Object.create(TreeNode.prototype);

LeafNode.prototype.generateHtml = function() {
  var html = '';

  html += '<li>\n';
  html += '  <a href="' + this.url + '">' + this.name + '</a>\n';
  html += '</li>\n';

  return html;
}

var TreeView = function(assets) {
  this.assets = assets;

  this.nodes = {};
  this.root = new TreeNode('.');
  this.nodes['.'] = this.root;

  for(var i in assets) {
    var node = new LeafNode(assets[i]);
    this.addNode(node);
  }
}

TreeView.prototype.getNode = function(id) {
  console.log(">>> getNode", id);

  if (id in this.nodes) {
    return this.nodes[id];
  }
  else {
    var node = new TreeNode(id);
    this.addNode(node);
    return node;
  }
}

TreeView.prototype.addNode = function(node) {
  this.nodes[node.id] = node;

  var parent = this.getNode(node.parent);
  parent.kids.push(node);

  console.log(">>> addNode", node.id, node.name, node.parent);
}

TreeView.prototype.generateHtml = function() {

  tree = '<div class="css-treeview">\n';
  tree += '<ul>\n';
  tree += this.root.generateHtml();
  tree += '</ul>\n';
  tree += '</div>\n';

  return tree;
}

module.exports = { TreeView: TreeView };

