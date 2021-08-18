import QtQuick 2.15
import QtQuick3D 1.15
import QtQuick3D.Helpers 1.15


View3D {
    id: view
    anchors.fill: parent

    environment: SceneEnvironment {
        clearColor: "#000033"
        backgroundMode: SceneEnvironment.Color
    }

    Node {
        id: scene

        PerspectiveCamera {
            id: camera
            z: 0
            x: 800
            y: 800
            eulerRotation: camera.lookAt(Qt.vector3d(0,0,0))
        }

        DirectionalLight {
            z: 300
            x: 300
            y: 300
            brightness: 100
            eulerRotation: Qt.vector3d(45, 45, -45)
        }

        //AxisHelper {
        //    enableAxisLines: true
        //}

        Axes {objectName: "UVW"; axis_1: "U"; axis_2: "V"; axis_3: "W"; position: Qt.vector3d(0, 0, -400)}
        Axes {objectName: "uvw"; axis_1: "u"; axis_2: "v"; axis_3: "w"; position: Qt.vector3d(0, 0, 0)}
        Axes {objectName: "xyz"; axis_1: "x"; axis_2: "y"; axis_3: "z"; position: Qt.vector3d(0, 0, 400)}
        
    }
}