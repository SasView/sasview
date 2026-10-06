Creating a Perspective
======================

This tutorial will walk you through the basic steps of creating a new perspective.

Creating the Perspective class
------------------------------------

All perspective need to be based on the `Perspective` base class. In doing so, you must override some methods which tell the data explorer the type of data the perspective can accept:

+ `supported_data`: this property returns a set of the different data it expects. For most perspectives, this may only be `SasData`, but you may also want to add `Trend`.
+ ``supports_multiple_data``: this returns a boolean flag. If its set to ``False``, the user can only send one data object to it. Generally, you'll want to keep this as ``False`` unless your perspective does consider multiple data objects *at the same time*. While previously perspectives had tabs, this is no longer the case. If the user wants to analyse multiple data objects at the same time, they are now encouraged to create multiple instances of the perspective. Therefore, perspectives shouldn't implement tabbing logic themselves.

  `Perspective` itself is based on `QDialog`, meaning the persepective class you create will also be a Dialog class, so you can add your GUI components to that object as well.

