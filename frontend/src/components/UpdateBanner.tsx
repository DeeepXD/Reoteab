import { useState } from "react";
import "./UpdateBanner.css";

interface UpdateBannerProps {
    version: string;
    currentVersion: string;
    downloadUrl: string;
    updateStatus: string | null;
    onDismiss?: () => void;
}

export default function UpdateBanner({ version, currentVersion, downloadUrl, updateStatus, onDismiss }: UpdateBannerProps) {
    const [isUpdatingLocal, setIsUpdatingLocal] = useState(false);

    const handleUpdate = async () => {
        setIsUpdatingLocal(true);
        try {
            if (window.pywebview && window.pywebview.api) {
                await window.pywebview.api.apply_update(downloadUrl, version);
            }
        } catch (e) {
            setIsUpdatingLocal(false);
        }
    };

    const handleViewRelease = () => {
        window.pywebview?.api?.open_url(`https://github.com/DeeepXD/Reoteab/releases/tag/${encodeURIComponent(version)}`);
    };

    const failed = updateStatus === "failed";
    const isDone = updateStatus?.startsWith("done|") ?? false;
    const doneFilename = isDone ? updateStatus!.split("|")[1] : "";
    const isUpdating = isUpdatingLocal || updateStatus === "downloading";

    if ((failed || isDone) && isUpdatingLocal) {
        setIsUpdatingLocal(false);
    }

    return (
        <div className={`update-banner ${failed ? "update-banner-error" : ""} ${isDone ? "update-banner-success" : ""}`}>
            <div className="update-banner-content">
                <span className="update-icon">
                    {failed ? "⚠️" : isDone ? "✅" : "❗"}
                </span>
                <span className="update-text">
                    {failed
                        ? "Update failed. Please try downloading again."
                        : isDone
                            ? `Updated! ${doneFilename || "Restarting"}`
                            : isUpdating
                                ? "Downloading update..."
                                : `Update available from the official Reoteab GitHub release. Current: ${currentVersion}. Latest: ${version}.`
                    }
                </span>
            </div>
            {!isUpdating && !isDone && (
                <div className="update-banner-actions">
                    <button className="update-btn update-btn-primary" onClick={handleUpdate}>
                        {failed ? "Retry Update" : "Update Now"}
                    </button>
                    <button className="update-btn update-btn-secondary" onClick={handleViewRelease}>
                        View Release
                    </button>
                    <button className="update-btn update-btn-secondary" onClick={onDismiss}>
                        Later
                    </button>
                </div>
            )}
            {isUpdating && !failed && !isDone && (
                <div className="update-spinner" />
            )}
        </div>
    );
}
