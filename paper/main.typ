#import "@preview/ctheorems:1.1.3": *
#import "@preview/unequivocal-ams:0.1.2": ams-article
#import "@preview/cetz:0.3.2"

#show: ams-article.with(
  title: [VertexPrint: 3D-printed joint-and-strut constructions for sparse, resizable models],
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
      fabrication of sparse and easily resizable 3D models. Operating on
      low-poly meshes, VertexPrint achieves its sparsity by printing out small
      joint components positioned at vertices and substituting connecting edges
      with cut-to-length struts. Models can be resized by rescaling struts,
      without reprinting vertex pieces. As struts can be made of inexpensive
      materials considerably stronger than printed parts, the resulting models
      can be scaled to sizes significantly larger than the limited volumes of
      conventional 3D printers.
    ],
    bibliography: bibliography("refs.bib"),
)

= Introduction

= Related Work
== Low-Fidelity Fabrication
_Low fidelity fabrication_

== Large-Volume 3D Printing
== Printing wireframes

= VertexPrint
== How VertexPrint Works
== Mechanical design of vertex pieces

= Implementation

= Validation

= Conclusion

= Acknowledgements
