#import "@preview/ctheorems:1.1.3": *
#import "@preview/unequivocal-ams:0.1.2": ams-article
#import "@preview/cetz:0.3.2"

#show: ams-article.with(
  title: [VertexPrint: 3D-printed joint-and-strut parts for sparse, resizable models],
    authors: (
      (
        name: "Devansh Vimal",
        email: "dvp0@asu.edu",
        url: "agentelement.net",
        organization: "Biodesign Center for Biocomputing, Security and Society, Arizona State University",
        location: "Tempe, Arizona, 85281"
      ),
    ),
    abstract: [
      This paper presents VertexPrint, a method that allows the rapid
      fabrication of sparse and easily resizable 3D models. VertexPrint
      operates on meshes and achieves its sparsity by printing out small joint
      components positioned at vertices and substitutes connecting edges with
      cut-to-length struts. Models can be resized by rescaling struts, without
      reprinting vertex pieces.
    ],
    bibliography: bibliography("refs.bib"),
)
