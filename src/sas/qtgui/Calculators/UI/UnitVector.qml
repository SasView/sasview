import QtQuick 2.15
import QtQuick3D 1.15
import QtQuick3D.Helpers 1.15

// This file contains the Vector object used to display unit vector properties. It contains a single vector with label M which
// can be set with the property label_text. This label is offset from the arrow head so that it passes outside the axis labels.
// The colour can be set with the property vector_color. The polar angles of the vector are set with angle_theta and angle_phi
// where theta is the polar angle from the z axis and phi the azimuthal angle in the x-y plane

Node {
    id: mainNode
    objectName: ""
    property alias vector_text: vector_label.text
    property string vector_color: "black"
    // rotation is in order xyz - using extrinsic axes - e.g. axes don't rotate with object
    rotation: Qt.quaternion(1, 0, 0, 0)
    position: Qt.vector3d(0, 0, 0)

    Model {
        id: arrow
        // after scaling cylinder is 10x10x100
        source: "#Cylinder"
        scale: Qt.vector3d(0.06, 0.7, 0.06)
        materials: DefaultMaterial {
            diffuseColor: mainNode.vector_color
            emissiveFactor: 0.5
        }
        eulerRotation: Qt.vector3d(90, 0, 0)
        position: Qt.vector3d(0, 0, 35)
    }

    Model {
        id: arrowhead
        // after scaling cone is 20x20x20
        source: "#Cone"
        scale: Qt.vector3d(0.2, 0.2, 0.2)
        materials: DefaultMaterial {
            diffuseColor: mainNode.vector_color
            emissiveFactor: 0.5
        }
        eulerRotation: Qt.vector3d(90, 0, 0)
        position: Qt.vector3d(0, 0, 70)
    }

    Node {
        Text {
            id: vector_label
            text: "M"
            font.pixelSize: 40
            color: mainNode.vector_color
        }
        eulerRotation: Qt.vector3d(-45, 90, 90)
        position: Qt.vector3d(0, 0, 180)
    }
}