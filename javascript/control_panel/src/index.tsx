import "./index.scss";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { ControlPanel } from "./ControlPanel";
import { Overlay } from "./Overlay";
import { Animations } from "./Animations";
import { convertTimeHmsStringToMs } from "./utils";
import { DataProvider } from "./DataProvider";
import { Stopwatch } from "./Stopwatch";
import { WheelPage } from "./Wheel";
import { WordGame } from "./WordGame";

const router = createBrowserRouter([
  {
    path: "/",
    element: <ControlPanel />,
  },
  {
    path: "/overlay",
    element: <Overlay />,
  },
  {
    path: "/overlaywithtimer",
    element: <Overlay timerMs={convertTimeHmsStringToMs("5m")} />,
  },
  {
    path: "/animations",
    element: <Animations />,
  },
  {
    path: "/stopwatch",
    element: <Stopwatch />,
  },
  {
    path: "/wheel",
    element: <WheelPage />,
  },
  {
    path: "/wordgame",
    element: <WordGame />,
  },
]);

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <DataProvider>
    <RouterProvider router={router} />
  </DataProvider>
);
