"""
Library Analysis Tool
Analyzes Python libraries from PyPI for license compliance and security assessment
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class LibraryAnalyzer:
    """Analyzes Python libraries from PyPI"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        
    def get_library_info(self, library_name: str) -> Dict[str, Any]:
        """Get comprehensive library information from PyPI"""
        try:
            url = f'https://pypi.org/pypi/{library_name}/json'
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code != 200:
                return {
                    'name': library_name,
                    'error': f'Not found on PyPI (status: {response.status_code})'
                }
                
            data = response.json()
            info = data.get('info', {})
            releases = data.get('releases', {})
            
            # Get latest release date
            latest_version = info.get('version', 'N/A')
            latest_release_date = None
            if latest_version in releases and releases[latest_version]:
                upload_time = releases[latest_version][0].get('upload_time', '')
                if upload_time:
                    latest_release_date = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
            
            # Extract license info from classifiers
            classifiers = info.get('classifiers', [])
            license_classifiers = [c for c in classifiers if 'License' in c and 'OSI Approved' in c]
            
            # Get project URLs
            project_urls = info.get('project_urls', {})
            
            return {
                'name': info.get('name', library_name),
                'version': latest_version,
                'summary': info.get('summary', 'N/A'),
                'license': info.get('license', 'N/A'),
                'license_classifiers': license_classifiers,
                'author': info.get('author', 'N/A'),
                'maintainer': info.get('maintainer', 'N/A'),
                'last_updated': latest_release_date,
                'last_updated_str': latest_release_date.strftime('%Y-%m-%d') if latest_release_date else 'N/A',
                'requires_python': info.get('requires_python', 'N/A'),
                'home_page': info.get('home_page', 'N/A'),
                'project_urls': project_urls,
                'keywords': info.get('keywords', 'N/A'),
                'download_url': info.get('download_url', 'N/A'),
                'bugtrack_url': info.get('bugtrack_url', 'N/A'),
                'docs_url': info.get('docs_url', 'N/A'),
                'classifiers': classifiers
            }
            
        except Exception as e:
            return {
                'name': library_name,
                'error': str(e)
            }
    
    def assess_library(self, lib_info: Dict[str, Any]) -> Dict[str, Any]:
        """Assess library based on security and compliance criteria"""
        assessment = {
            'recommendation': 'UNKNOWN',
            'score': 0,
            'issues': [],
            'warnings': [],
            'positives': []
        }
        
        if 'error' in lib_info:
            assessment['recommendation'] = 'ERROR'
            assessment['issues'].append(f"Cannot retrieve info: {lib_info['error']}")
            return assessment
        
        score = 0
        
        # Check license
        license_info = lib_info.get('license', 'N/A')
        license_classifiers = lib_info.get('license_classifiers', [])
        
        if license_classifiers:
            score += 30
            assessment['positives'].append("OSI Approved license found")
        elif license_info and license_info.lower() not in ['n/a', 'none', '']:
            if any(keyword in license_info.lower() for keyword in ['mit', 'apache', 'bsd', 'gpl', 'lgpl']):
                score += 20
                assessment['positives'].append(f"Open source license: {license_info}")
            else:
                assessment['warnings'].append(f"Unknown license: {license_info}")
        else:
            assessment['issues'].append("No license information available")
        
        # Check last update
        last_updated = lib_info.get('last_updated')
        if last_updated:
            days_since_update = (datetime.now(last_updated.tzinfo) - last_updated).days
            if days_since_update <= 90:
                score += 25
                assessment['positives'].append(f"Recently updated ({days_since_update} days ago)")
            elif days_since_update <= 365:
                score += 15
                assessment['warnings'].append(f"Updated {days_since_update} days ago")
            else:
                assessment['issues'].append(f"Not updated for {days_since_update} days")
        else:
            assessment['warnings'].append("Cannot determine last update date")
        
        # Check Python version compatibility
        requires_python = lib_info.get('requires_python', 'N/A')
        if requires_python and requires_python != 'N/A':
            score += 10
            assessment['positives'].append(f"Python version requirements specified: {requires_python}")
        
        # Check documentation
        home_page = lib_info.get('home_page', 'N/A')
        docs_url = lib_info.get('docs_url', 'N/A')
        project_urls = lib_info.get('project_urls', {})
        
        if any([home_page != 'N/A', docs_url != 'N/A', project_urls]):
            score += 10
            assessment['positives'].append("Documentation/homepage available")
        
        # Check maintainer info
        author = lib_info.get('author', 'N/A')
        maintainer = lib_info.get('maintainer', 'N/A')
        if any([author != 'N/A', maintainer != 'N/A']):
            score += 10
            assessment['positives'].append("Author/maintainer information available")
        
        # Final recommendation
        assessment['score'] = score
        if score >= 70:
            assessment['recommendation'] = 'RECOMMENDED'
        elif score >= 50:
            assessment['recommendation'] = 'CONDITIONALLY_RECOMMENDED'
        elif score >= 30:
            assessment['recommendation'] = 'NEEDS_REVIEW'
        else:
            assessment['recommendation'] = 'NOT_RECOMMENDED'
        
        return assessment
    
    def analyze_libraries(self, libraries: List[str]) -> Dict[str, Dict[str, Any]]:
        """Analyze multiple libraries"""
        results = {}
        
        for lib in libraries:
            print(f"Analyzing {lib}...")
            lib_info = self.get_library_info(lib)
            assessment = self.assess_library(lib_info)
            
            results[lib] = {
                'info': lib_info,
                'assessment': assessment
            }
        
        return results
    
    def print_detailed_report(self, results: Dict[str, Dict[str, Any]]):
        """Print detailed analysis report"""
        print("\n" + "="*80)
        print("LIBRARY ANALYSIS REPORT")
        print("="*80)
        
        recommendations = {
            'RECOMMENDED': [],
            'CONDITIONALLY_RECOMMENDED': [],
            'NEEDS_REVIEW': [],
            'NOT_RECOMMENDED': [],
            'ERROR': []
        }
        
        for lib_name, data in results.items():
            info = data['info']
            assessment = data['assessment']
            recommendation = assessment['recommendation']
            
            recommendations[recommendation].append(lib_name)
            
            print(f"\n📦 {lib_name.upper()}")
            print("-" * 50)
            
            if 'error' in info:
                print(f"❌ ERROR: {info['error']}")
                continue
            
            # Basic info
            print(f"Name: {info['name']}")
            print(f"Version: {info['version']}")
            print(f"Summary: {info['summary']}")
            print(f"Author: {info['author']}")
            if info['maintainer'] != 'N/A':
                print(f"Maintainer: {info['maintainer']}")
            
            # License info
            license_info = info['license']
            license_classifiers = info['license_classifiers']
            if license_classifiers:
                print(f"License: {' | '.join(license_classifiers)}")
            elif license_info != 'N/A':
                print(f"License: {license_info}")
            else:
                print("License: ❌ Not specified")
            
            # Update info
            print(f"Last Updated: {info['last_updated_str']}")
            print(f"Python Required: {info['requires_python']}")
            
            # URLs
            if info['home_page'] != 'N/A':
                print(f"Homepage: {info['home_page']}")
            
            project_urls = info['project_urls']
            if project_urls:
                print("Project URLs:")
                for key, url in project_urls.items():
                    print(f"  {key}: {url}")
            
            # Assessment
            score = assessment['score']
            rec_emoji = {
                'RECOMMENDED': '✅',
                'CONDITIONALLY_RECOMMENDED': '⚠️',
                'NEEDS_REVIEW': '🔍',
                'NOT_RECOMMENDED': '❌'
            }
            
            print(f"\n{rec_emoji.get(recommendation, '❓')} RECOMMENDATION: {recommendation}")
            print(f"📊 Score: {score}/100")
            
            if assessment['positives']:
                print("✅ Positives:")
                for positive in assessment['positives']:
                    print(f"  • {positive}")
            
            if assessment['warnings']:
                print("⚠️ Warnings:")
                for warning in assessment['warnings']:
                    print(f"  • {warning}")
            
            if assessment['issues']:
                print("❌ Issues:")
                for issue in assessment['issues']:
                    print(f"  • {issue}")
        
        # Summary
        print(f"\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        total_libs = len(results)
        for rec_type, libs in recommendations.items():
            if libs:
                count = len(libs)
                percentage = (count / total_libs) * 100
                emoji = {
                    'RECOMMENDED': '✅',
                    'CONDITIONALLY_RECOMMENDED': '⚠️',
                    'NEEDS_REVIEW': '🔍',
                    'NOT_RECOMMENDED': '❌',
                    'ERROR': '💥'
                }
                print(f"{emoji.get(rec_type, '❓')} {rec_type}: {count} libraries ({percentage:.1f}%)")
                for lib in libs:
                    print(f"   • {lib}")
        
        print(f"\nTotal libraries analyzed: {total_libs}")


def main():
    """Main entry point for library analysis"""
    if len(sys.argv) < 2:
        print("Usage: python -m mcp_server.libs.analyzer <library1> [library2] ...")
        print("Example: python -m mcp_server.libs.analyzer langchain requests numpy")
        sys.exit(1)
    
    libraries = sys.argv[1:]
    
    print(f"🔍 Starting analysis of {len(libraries)} library(ies)...")
    print(f"Libraries to analyze: {', '.join(libraries)}")
    
    analyzer = LibraryAnalyzer()
    results = analyzer.analyze_libraries(libraries)
    analyzer.print_detailed_report(results)


if __name__ == "__main__":
    main()
