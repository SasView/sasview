import QtQuick 2.15
import QtQuick3D 1.15
import QtQuick3D.Helpers 1.15

Node {
    id: mainNode
    objectName: ""
    property alias axis_1: x_axis_label.text
    property alias axis_2: y_axis_label.text
    property alias axis_3: z_axis_label.text 
    // rotation is in order xyz - using extrinsic axes - e.g. axes don't rotate with object
    rotation: Qt.quaternion(1, 0, 0, 0)
    position: Qt.vector3d(0, 0, 0)

    Model {
        // after scaling cylinder is 10x10x100
        source: "#Cylinder"
        scale: Qt.vector3d(0.1, 1, 0.1)
        materials: DefaultMaterial {
            diffuseColor: "red"
            emissiveFactor: 0.5
        }
        eulerRotation: Qt.vector3d(0, 0, -90)
        position: Qt.vector3d(50, 0, 0)
    }

    Model {
        // after scaling cone is 20x20x20
        source: "#Cone"
        scale: Qt.vector3d(0.2, 0.2, 0.2)
        materials: DefaultMaterial {
            diffuseColor: "red"
            emissiveFactor: 0.5
        }
        eulerRotation: Qt.vector3d(0, 0, -90)
        position: Qt.vector3d(100, 0, 0)
    }

    Node {
        Text {
            id: x_axis_label
            text: "U"
            font.pixelSize: 40
            color: "red"
        }
        eulerRotation: Qt.vector3d(-45, 0, -90)
        position: Qt.vector3d(140, 0, 0)
    }

    Model {
        source: "#Cylinder"
        scale: Qt.vector3d(0.1, 1, 0.1)
        materials: DefaultMaterial {
            diffuseColor: "green"
            emissiveFactor: 0.5
        }
        eulerRotation: Qt.vector3d(0, 0, 0)
        position: Qt.vector3d(0, 50, 0)
    }

    Model {
        source: "#Cone"
        scale: Qt.vector3d(0.2, 0.2, 0.2)
        materials: DefaultMaterial {
            diffuseColor: "green"
            emissiveFactor: 0.5
        }
        eulerRotation: Qt.vector3d(0, 0, 0)
        position: Qt.vector3d(0, 100, 0)
    }

    Node {
        Text {
            id: y_axis_label
            text: "V"
            font.pixelSize: 40
            color: "green"
        }
        eulerRotation: Qt.vector3d(0, 45, 0)
        position: Qt.vector3d(0, 140, 0)
    }

    Model {
        source: "#Cylinder"
        scale: Qt.vector3d(0.1, 1, 0.1)
        materials: DefaultMaterial {
            diffuseColor: "blue"
            emissiveFactor: 0.5
        }
        eulerRotation: Qt.vector3d(90, 0, 0)
        position: Qt.vector3d(0, 0, 50)
    }

    Model {
        source: "#Cone"
        scale: Qt.vector3d(0.2, 0.2, 0.2)
        materials: DefaultMaterial {
            diffuseColor: "blue"
            emissiveFactor: 0.5
        }
        eulerRotation: Qt.vector3d(90, 0, 0)
        position: Qt.vector3d(0, 0, 100)
    }

    Node {
        Text {
            id: z_axis_label
            text: "W"
            font.pixelSize: 40
            color: "blue"
        }
        eulerRotation: Qt.vector3d(-45, 90, 90)
        position: Qt.vector3d(0, 0, 140)
    }
}