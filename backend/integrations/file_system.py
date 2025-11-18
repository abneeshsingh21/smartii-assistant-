"""
File System Operations for SMARTII
Provides file search, organization, and management capabilities
"""

import logging
import os
import shutil
import glob
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class FileSystemManager:
    """Advanced file system operations"""
    
    def __init__(self):
        self.common_folders = {
            "desktop": os.path.expanduser("~/Desktop"),
            "documents": os.path.expanduser("~/Documents"),
            "downloads": os.path.expanduser("~/Downloads"),
            "pictures": os.path.expanduser("~/Pictures"),
            "music": os.path.expanduser("~/Music"),
            "videos": os.path.expanduser("~/Videos"),
        }
    
    def search_files(self, query: str, location: Optional[str] = None, file_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for files
        
        Args:
            query: Search query (filename pattern)
            location: Folder to search in (desktop, documents, downloads, etc.)
            file_type: File extension filter (.pdf, .txt, etc.)
            limit: Maximum results
            
        Returns:
            List of matching files with metadata
        """
        try:
            logger.info(f"Searching files: query={query}, location={location}, type={file_type}")
            
            # Determine search path
            if location and location.lower() in self.common_folders:
                search_path = self.common_folders[location.lower()]
            else:
                search_path = location or os.path.expanduser("~")
            
            if not os.path.exists(search_path):
                return []
            
            results = []
            pattern = f"*{query}*"
            
            # Add file type filter
            if file_type:
                if not file_type.startswith('.'):
                    file_type = f".{file_type}"
                pattern = f"*{query}*{file_type}"
            
            # Search recursively
            for root, dirs, files in os.walk(search_path):
                for filename in files:
                    if query.lower() in filename.lower():
                        # Check file type
                        if file_type and not filename.endswith(file_type):
                            continue
                        
                        filepath = os.path.join(root, filename)
                        
                        try:
                            stat = os.stat(filepath)
                            results.append({
                                "name": filename,
                                "path": filepath,
                                "size": stat.st_size,
                                "size_formatted": self._format_size(stat.st_size),
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                                "extension": os.path.splitext(filename)[1],
                                "directory": os.path.dirname(filepath)
                            })
                            
                            if len(results) >= limit:
                                break
                        except Exception as e:
                            logger.debug(f"Error accessing {filepath}: {e}")
                            continue
                
                if len(results) >= limit:
                    break
            
            logger.info(f"Found {len(results)} matching files")
            return results
            
        except Exception as e:
            logger.error(f"File search error: {e}")
            return []
    
    def find_recent_files(self, location: str = "downloads", hours: int = 24, limit: int = 20) -> List[Dict[str, Any]]:
        """Find recently modified files"""
        try:
            search_path = self.common_folders.get(location.lower(), os.path.expanduser("~/Downloads"))
            
            if not os.path.exists(search_path):
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            results = []
            
            for root, dirs, files in os.walk(search_path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    
                    try:
                        stat = os.stat(filepath)
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        
                        if mtime > cutoff_time:
                            results.append({
                                "name": filename,
                                "path": filepath,
                                "size": stat.st_size,
                                "size_formatted": self._format_size(stat.st_size),
                                "modified": mtime.isoformat(),
                                "extension": os.path.splitext(filename)[1]
                            })
                    except:
                        continue
            
            # Sort by modification time (most recent first)
            results.sort(key=lambda x: x["modified"], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error finding recent files: {e}")
            return []
    
    def organize_folder(self, folder_path: str, by: str = "type") -> Dict[str, Any]:
        """
        Organize files in a folder
        
        Args:
            folder_path: Path to folder to organize
            by: Organization method (type, date, size)
            
        Returns:
            Summary of organization
        """
        try:
            logger.info(f"Organizing folder: {folder_path} by {by}")
            
            if not os.path.exists(folder_path):
                return {"success": False, "error": "Folder not found"}
            
            moved_files = []
            
            if by == "type":
                # Group by file extension
                type_folders = {
                    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".pptx"],
                    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
                    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
                    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
                    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
                    "Code": [".py", ".js", ".html", ".css", ".java", ".cpp"],
                }
                
                for filename in os.listdir(folder_path):
                    filepath = os.path.join(folder_path, filename)
                    
                    if os.path.isfile(filepath):
                        ext = os.path.splitext(filename)[1].lower()
                        
                        # Find category
                        category = "Other"
                        for cat, extensions in type_folders.items():
                            if ext in extensions:
                                category = cat
                                break
                        
                        # Create category folder
                        category_path = os.path.join(folder_path, category)
                        os.makedirs(category_path, exist_ok=True)
                        
                        # Move file
                        try:
                            dest_path = os.path.join(category_path, filename)
                            shutil.move(filepath, dest_path)
                            moved_files.append({
                                "file": filename,
                                "category": category,
                                "from": filepath,
                                "to": dest_path
                            })
                        except Exception as e:
                            logger.error(f"Error moving {filename}: {e}")
            
            return {
                "success": True,
                "organized_by": by,
                "files_moved": len(moved_files),
                "details": moved_files
            }
            
        except Exception as e:
            logger.error(f"Folder organization error: {e}")
            return {"success": False, "error": str(e)}
    
    def find_duplicates(self, folder_path: str) -> List[List[str]]:
        """Find duplicate files in folder"""
        try:
            logger.info(f"Finding duplicates in: {folder_path}")
            
            if not os.path.exists(folder_path):
                return []
            
            # Dictionary to store file hashes
            hash_dict = {}
            
            for root, dirs, files in os.walk(folder_path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    
                    try:
                        # Calculate file hash
                        file_hash = self._calculate_file_hash(filepath)
                        
                        if file_hash in hash_dict:
                            hash_dict[file_hash].append(filepath)
                        else:
                            hash_dict[file_hash] = [filepath]
                    except:
                        continue
            
            # Find duplicates
            duplicates = [paths for paths in hash_dict.values() if len(paths) > 1]
            
            logger.info(f"Found {len(duplicates)} sets of duplicate files")
            return duplicates
            
        except Exception as e:
            logger.error(f"Duplicate detection error: {e}")
            return []
    
    def get_folder_size(self, folder_path: str) -> Dict[str, Any]:
        """Calculate total size of folder"""
        try:
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(folder_path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                        file_count += 1
                    except:
                        continue
            
            return {
                "path": folder_path,
                "size_bytes": total_size,
                "size_formatted": self._format_size(total_size),
                "file_count": file_count
            }
            
        except Exception as e:
            logger.error(f"Folder size calculation error: {e}")
            return {"error": str(e)}
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def _calculate_file_hash(self, filepath: str, algorithm: str = 'md5') -> str:
        """Calculate file hash"""
        hash_algo = hashlib.md5()
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_algo.update(chunk)
        
        return hash_algo.hexdigest()


# Global instance
_file_system_manager = None


def get_file_system_manager() -> FileSystemManager:
    """Get or create global file system manager instance"""
    global _file_system_manager
    if _file_system_manager is None:
        _file_system_manager = FileSystemManager()
    return _file_system_manager
